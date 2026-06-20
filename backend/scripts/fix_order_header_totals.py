#!/usr/bin/env python3
"""
Recalculate order header totals from active line items (fixes stale subtotal bug).

Usage:
  cd backend && python scripts/fix_order_header_totals.py 606 --dry-run
  cd backend && python scripts/fix_order_header_totals.py 606 --apply
  cd backend && python scripts/fix_order_header_totals.py 554 --partial-paid 67 --force --dry-run
  cd backend && python scripts/fix_order_header_totals.py 554 --partial-paid 67 --force --apply
"""
import argparse
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import Config
from constants.status_enums import OrderStatus, PaymentStatus
from models import db
from models.order import Order
from utils.money import round_money
from utils.order_audit import active_items_for_order
from utils.order_totals import calculate_amount_due, sync_order_pricing


def resolve_order(ref):
    if str(ref).isdigit():
        return Order.query.filter_by(id=int(ref), deleted_at=None).first()
    return Order.query.filter_by(order_number=str(ref), deleted_at=None).first()


def order_snapshot(order):
    line_sum = sum(Decimal(str(i.total_price or 0)) for i in active_items_for_order(order.id))
    return {
        'id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'payment_status': order.payment_status,
        'subtotal': float(order.subtotal or 0),
        'line_sum': float(line_sum),
        'delta': float(line_sum - Decimal(str(order.subtotal or 0))),
        'shipping_fee': float(order.shipping_fee or 0),
        'total': float(order.total or 0),
        'amount_due': float(calculate_amount_due(order)),
        'store_credit_applied': float(order.store_credit_applied or 0),
        'adjustment_amount': float(order.adjustment_amount or 0),
        'adjustment_notes': order.adjustment_notes,
        'points_earned': order.points_earned,
    }


def apply_partial_paid_reconcile(order, partial_paid: Decimal):
    """
    Fix line/header mismatch when customer already paid part of the order.
    Sets subtotal from lines, records prior payment as negative adjustment,
    leaves payment_status unpaid for the remaining balance.
    Preserves points_earned and payment_date from the original payment.
    """
    prior_points = order.points_earned
    prior_payment_date = order.payment_date
    sync_order_pricing(order, reprice_lines=False)
    paid = round_money(partial_paid)
    order.adjustment_amount = -paid
    note = f'已付 ${paid}（原订单金额）；余款待收'
    if order.adjustment_notes:
        order.adjustment_notes = f'{order.adjustment_notes.strip()}\n{note}'
    else:
        order.adjustment_notes = note
    order.payment_status = PaymentStatus.UNPAID.value
    order.points_earned = prior_points
    order.payment_date = prior_payment_date
    # Keep gross total (subtotal + shipping) for display; amount_due uses adjustment separately.
    order.total = round_money(order.subtotal + order.shipping_fee)


def can_fix(order, force=False):
    if force:
        return True, None
    if order.payment_status == PaymentStatus.PAID.value:
        return False, 'order is paid — use --force to override'
    if order.status == OrderStatus.COMPLETED.value:
        return False, 'order is completed — use --force to override'
    return True, None


def main():
    parser = argparse.ArgumentParser(description='Recalculate order header from active lines')
    parser.add_argument('order', help='Order id or order_number')
    parser.add_argument('--dry-run', action='store_true', help='Show before/after only')
    parser.add_argument('--apply', action='store_true', help='Persist recalculated totals')
    parser.add_argument('--force', action='store_true', help='Allow fix on paid/completed orders')
    parser.add_argument(
        '--partial-paid',
        type=Decimal,
        default=None,
        help='Record amount already collected; sets adjustment and unpaid balance (requires --force)',
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        parser.error('Specify --dry-run or --apply')

    cfg = Config()
    if cfg.MYSQL_DATABASE == 'gsf_app':
        print('WARNING: connected to prod database (gsf_app).\n')

    app, _ = create_app()
    with app.app_context():
        order = resolve_order(args.order)
        if not order:
            print(f'Order not found: {args.order}')
            sys.exit(1)

        ok, reason = can_fix(order, force=args.force or args.partial_paid is not None)
        if not ok:
            print(f'Refusing to fix order {order.order_number}: {reason}')
            sys.exit(1)

        if args.partial_paid is not None and not args.force:
            print('--partial-paid requires --force for paid/completed orders')
            sys.exit(1)

        before = order_snapshot(order)
        print('Before:', before)

        if args.partial_paid is not None:
            apply_partial_paid_reconcile(order, args.partial_paid)
        else:
            sync_order_pricing(order, reprice_lines=False)
        after = order_snapshot(order)
        print('After: ', after)

        if abs(after['delta']) > 0.01:
            print('WARNING: line sum still differs from subtotal after recalc')
            if args.apply:
                db.session.rollback()
                sys.exit(1)

        if args.dry_run:
            db.session.rollback()
            print('Dry run — no changes saved.')
            return

        db.session.commit()
        print(f'Applied fix for order {order.order_number} (#{order.id}).')


if __name__ == '__main__':
    main()
