#!/usr/bin/env python3
"""
One-time (or safe to re-run): assign referral_code to every user who has at least one
completed order and does not yet have a code.

Uses referral_service.generate_unique_referral_code() — REFERRAL_CODE_LENGTH (8) chars,
alphanumeric without ambiguous 0/O/1/I; uniqueness enforced against users.referral_code.

Run from repo backend directory:
  python scripts/backfill_referral_codes.py
  python scripts/backfill_referral_codes.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app  # noqa: E402
from constants.status_enums import OrderStatus  # noqa: E402
from models import db  # noqa: E402
from models.order import Order  # noqa: E402
from models.user import User  # noqa: E402
from services import referral_service  # noqa: E402


def user_ids_with_completed_order():
    rows = (
        db.session.query(Order.user_id)
        .filter(
            Order.status == OrderStatus.COMPLETED.value,
            Order.deleted_at.is_(None),
        )
        .distinct()
        .all()
    )
    return sorted({r[0] for r in rows})


def main():
    parser = argparse.ArgumentParser(description='Backfill referral_code for users with completed orders.')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print actions only; do not write to the database.',
    )
    args = parser.parse_args()

    app, _ = create_app()
    with app.app_context():
        uids = user_ids_with_completed_order()
        print(f'Users with >=1 completed order (distinct): {len(uids)}')
        assigned = 0
        skipped = 0
        missing_user = 0

        for uid in uids:
            user = db.session.get(User, uid)
            if not user:
                missing_user += 1
                print(f'  ! skip user_id={uid} (row missing)')
                continue
            if user.referral_code:
                skipped += 1
                print(
                    f'  - skip user_id={uid} '
                    f'nickname={user.nickname!r} already code={user.referral_code}'
                )
                continue

            if args.dry_run:
                print(
                    f'  [dry-run] would assign user_id={uid} '
                    f'nickname={user.nickname!r} '
                    f'({referral_service.REFERRAL_CODE_LENGTH}-char unique code)'
                )
                assigned += 1
                continue

            code = referral_service.generate_unique_referral_code()
            user.referral_code = code
            db.session.add(user)
            db.session.commit()
            print(
                f'  + assigned user_id={uid} '
                f'nickname={user.nickname!r} -> {code}'
            )
            assigned += 1

        print(
            f'Done. assigned={assigned}, skipped_existing={skipped}, '
            f'missing_user_rows={missing_user}, dry_run={args.dry_run}'
        )


if __name__ == '__main__':
    main()
