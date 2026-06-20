#!/usr/bin/env python3
"""
Read-only audit: orders where header subtotal != sum(line total_price).

Usage:
  cd backend && python scripts/audit_order_total_mismatches.py
  cd backend && python scripts/audit_order_total_mismatches.py --group-deal-id 18
  cd backend && python scripts/audit_order_total_mismatches.py --material-only
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal

from app import create_app
from config import Config
from models.order import Order
from utils.order_totals import calculate_amount_due


def main():
    parser = argparse.ArgumentParser(description='Audit order subtotal vs line sums (read-only)')
    parser.add_argument('--group-deal-id', type=int, default=None)
    parser.add_argument('--material-only', action='store_true', help='Only |delta| > $0.01')
    args = parser.parse_args()

    cfg = Config()
    db_name = cfg.MYSQL_DATABASE
    if db_name == 'gsf_app':
        print('WARNING: connected to prod database (gsf_app). Read-only — no changes will be made.\n')

    app, _ = create_app()
    with app.app_context():
        q = Order.query.filter(Order.deleted_at.is_(None))
        if args.group_deal_id is not None:
            q = q.filter(Order.group_deal_id == args.group_deal_id)
        orders = q.order_by(Order.id).all()

        mismatches = []
        for o in orders:
            item_sum = sum(Decimal(str(i.total_price or 0)) for i in o.items)
            sub = Decimal(str(o.subtotal or 0))
            delta = item_sum - sub
            if abs(delta) <= Decimal('0.009'):
                continue
            if args.material_only and abs(delta) <= Decimal('0.01'):
                continue
            mismatches.append({
                'id': o.id,
                'order_number': o.order_number,
                'group_deal_id': o.group_deal_id,
                'status': o.status,
                'payment': o.payment_status,
                'subtotal': float(sub),
                'line_sum': float(item_sum),
                'delta': float(delta),
                'amount_due': float(calculate_amount_due(o)),
                'credit': float(o.store_credit_applied or 0),
                'adjustment': float(o.adjustment_amount or 0),
                'points': o.points_earned,
                'items': len(o.items),
            })

        scope = f'deal {args.group_deal_id}' if args.group_deal_id else 'all deals'
        print(f'Scanned {len(orders)} orders ({scope})')
        print(f'Mismatches: {len(mismatches)}')
        print('-' * 100)
        for m in mismatches:
            print(m)


if __name__ == '__main__':
    main()
