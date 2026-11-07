#!/usr/bin/env python3
"""Recalculate open orders after a bundled_weight min/max change.

Copies the product's current min_weight and max_weight onto each unpaid line
and reprices the estimate (rate × min_weight). Weighed lines keep
rate × final_weight. Paid, completed, and cancelled orders are left alone.

Usage:
  cd backend && python scripts/sync_bundled_weight_bounds.py --name 羊排骨 --dry-run
  cd backend && python scripts/sync_bundled_weight_bounds.py --name 羊排骨 --apply
  cd backend && python scripts/sync_bundled_weight_bounds.py --product-id 123 --apply
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from models.product import Product
from utils.product_price_choices import sync_bundled_weight_bounds_to_open_orders


def find_products(name, product_id):
    query = Product.query.filter(Product.deleted_at.is_(None))
    if product_id is not None:
        query = query.filter(Product.id == product_id)
    if name:
        query = query.filter(Product.name.contains(name))
    return query.order_by(Product.id).all()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', help='Product name contains this text')
    parser.add_argument('--product-id', type=int)
    parser.add_argument('--apply', action='store_true', help='Commit the recalculation')
    parser.add_argument('--dry-run', action='store_true', help='Print changes and roll back')
    args = parser.parse_args()
    if not args.name and args.product_id is None:
        parser.error('Pass --name or --product-id')
    if args.apply == args.dry_run:
        parser.error('Pass exactly one of --apply or --dry-run')

    app, _ = create_app()
    with app.app_context():
        products = find_products(args.name, args.product_id)
        if not products:
            print('No matching product')
            return 1
        if len(products) > 1:
            for product in products:
                print(f'{product.id}\t{product.pricing_type}\t{product.name}')
            print('More than one product matched. Re-run with --product-id.')
            return 1

        product = products[0]
        pricing = product.pricing_data or {}
        print(
            f'Product {product.id} {product.name} '
            f'min={pricing.get("min_weight")} max={pricing.get("max_weight")} '
            f'rate={pricing.get("price_per_unit")}'
        )
        if product.pricing_type != 'bundled_weight':
            print(f'Product pricing_type is {product.pricing_type}, not bundled_weight')
            return 1

        changes = sync_bundled_weight_bounds_to_open_orders(product)
        if not changes:
            print('No open lines needed a bounds update')
            db.session.rollback()
            return 0

        for row in changes:
            weight = row['final_weight']
            weight_label = f'{weight} lb' if weight is not None else 'unweighed'
            print(
                f"order {row['order_number']} (id {row['order_id']}, deal {row['group_deal_id']}) "
                f"item {row['item_id']} {weight_label}: "
                f"{row['old_total']} -> {row['new_total']}"
            )
        print(f'{len(changes)} line(s)')

        if args.apply:
            db.session.commit()
            print('Applied')
        else:
            db.session.rollback()
            print('Dry run, rolled back')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
