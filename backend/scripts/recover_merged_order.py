#!/usr/bin/env python3
"""
Recover order lines and notes after a bad merge (product_id-only aggregation).

Merges soft-deleted source orders back into the kept order, preserving each
original line (variants, weights). Reconstructs main-order lines that were
collapsed into combined rows.

Usage:
  python scripts/recover_merged_order.py GSF-20260522205706-NJRVRT --dry-run
  python scripts/recover_merged_order.py GSF-20260522205706-NJRVRT --apply
"""
import argparse
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from models.order import Order, OrderItem
from models.product import Product
from utils.order_item_pricing import combine_order_notes
from utils.order_totals import sync_order_pricing


def line_desc(item):
    p = Product.query.get(item.product_id)
    name = p.name if p else f'product#{item.product_id}'
    v = f' · {item.variant_name}' if item.variant_name else ''
    return f'{name}{v} qty={item.quantity} ${item.total_price}'


def snapshot_item(item):
    return {
        'product_id': item.product_id,
        'quantity': item.quantity,
        'unit_price': item.unit_price,
        'total_price': item.total_price,
        'final_weight': item.final_weight,
        'variant_id': item.variant_id,
        'variant_name': item.variant_name,
        'variant_price_delta': item.variant_price_delta,
        'accept_substitute': item.accept_substitute,
        'is_unavailable': item.is_unavailable,
    }


def merge_notes(orders):
    return combine_order_notes(orders)


def reconstruct_lines(main, deleted_orders):
    """
    Build line list: all lines from soft-deleted orders, plus main-order lines
    that were not fully represented (e.g. combined qty without variant).
    """
    lines = []
    seen_keys = set()

    def add_from_item(item, source):
        key = (item.product_id, item.variant_id, item.quantity, item.final_weight)
        if key in seen_keys:
            return
        seen_keys.add(key)
        lines.append((source, snapshot_item(item)))

    for order in deleted_orders:
        for item in order.items:
            add_from_item(item, order.order_number)

    # Quantities merged on main per product (without variant)
    deleted_qty_by_product = {}
    for order in deleted_orders:
        for item in order.items:
            deleted_qty_by_product[item.product_id] = (
                deleted_qty_by_product.get(item.product_id, 0) + item.quantity
            )

    for item in main.items:
        product = Product.query.get(item.product_id)
        if not product:
            continue
        has_deleted_same_product = any(
            di.product_id == item.product_id
            for o in deleted_orders
            for di in o.items
        )
        deleted_qty = deleted_qty_by_product.get(item.product_id, 0)
        main_qty = item.quantity or 0
        remainder = main_qty - deleted_qty

        if not has_deleted_same_product:
            add_from_item(item, f'{main.order_number}(main)')
            continue

        # Same product on both orders: keep main order's line as its own row (e.g. second 乳鸽).
        if item.variant_id or product.pricing_type in ('weight_range', 'unit_weight', 'bundled_weight'):
            add_from_item(item, f'{main.order_number}(main)')
        elif remainder <= 0:
            # Same product qty on deleted order(s), but a distinct line (e.g. 488 plain 蛋鸡 vs 519 variant).
            deleted_variants = {
                di.variant_id
                for o in deleted_orders
                for di in o.items
                if di.product_id == item.product_id
            }
            if item.variant_id not in deleted_variants:
                add_from_item(item, f'{main.order_number}(main)')
        else:
            unit = float(item.unit_price or 0)
            snap = snapshot_item(item)
            snap['quantity'] = remainder
            snap['unit_price'] = unit
            snap['total_price'] = round(unit * remainder, 2)
            snap['variant_id'] = None
            snap['variant_name'] = None
            key = (item.product_id, None, remainder, None)
            if key not in seen_keys:
                seen_keys.add(key)
                lines.append((f'{main.order_number}(remainder)', snap))

        if item.variant_id and not any(
            di.variant_id == item.variant_id and di.product_id == item.product_id
            for o in deleted_orders
            for di in o.items
        ):
            add_from_item(item, f'{main.order_number}(main)')

    return lines


def collect_deleted_sources(main):
    return (
        Order.query.filter(
            Order.user_id == main.user_id,
            Order.group_deal_id == main.group_deal_id,
            Order.deleted_at.isnot(None),
            Order.id != main.id,
        )
        .order_by(Order.created_at)
        .all()
    )


def apply_lines(main, line_entries, source_orders, dry_run):
    print(f'Restore {len(line_entries)} line(s) on {main.order_number} (id={main.id}):')
    for source, data in line_entries:
        p = Product.query.get(data['product_id'])
        v = f" · {data.get('variant_name')}" if data.get('variant_name') else ''
        print(f'  [{source}] {p.name if p else data["product_id"]}{v} qty={data["quantity"]}')

    new_notes = merge_notes([main] + list(source_orders))
    print(f'Combined notes:\n{new_notes!r}')

    if dry_run:
        print('\n(dry-run — pass --apply to write)')
        return

    OrderItem.soft_delete_for_order(main.id, db.session)
    for _source, data in line_entries:
        db.session.add(
            OrderItem(
                order_id=main.id,
                product_id=data['product_id'],
                quantity=data['quantity'],
                unit_price=data['unit_price'],
                total_price=data['total_price'],
                final_weight=data.get('final_weight'),
                variant_id=data.get('variant_id'),
                variant_name=data.get('variant_name'),
                variant_price_delta=data.get('variant_price_delta'),
                accept_substitute=data.get('accept_substitute'),
                is_unavailable=data.get('is_unavailable', False),
            )
        )
    main.notes = new_notes
    db.session.flush()
    sync_order_pricing(main)
    db.session.commit()
    print(f'\nApplied. subtotal={main.subtotal} total={main.total}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('order_number', help='Merged order number (kept order)')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    app, _ = create_app()
    with app.app_context():
        main = Order.query.filter(
            Order.order_number == args.order_number,
            Order.deleted_at.is_(None),
        ).first()
        if not main:
            print('Active order not found:', args.order_number)
            sys.exit(1)

        deleted = collect_deleted_sources(main)
        print('Deleted source orders:')
        for o in deleted:
            print(f'  {o.id} {o.order_number} items={len(o.items)} notes={repr((o.notes or "")[:60])}')

        lines = reconstruct_lines(main, deleted)
        apply_lines(main, lines, deleted, dry_run=not args.apply)


if __name__ == '__main__':
    main()
