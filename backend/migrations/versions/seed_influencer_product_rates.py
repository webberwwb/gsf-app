"""Seed influencer product rates from existing general-customer rules.

Revision ID: seed_influencer_product_rates
Revises: add_influencer_program
Create Date: 2026-09-07
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from alembic import op
import sqlalchemy as sa


revision = 'seed_influencer_product_rates'
down_revision = 'add_influencer_program'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    now = datetime.now(ZoneInfo('America/New_York')).replace(tzinfo=None)
    sdr = conn.execute(
        sa.text('SELECT id FROM sdrs WHERE is_active = 1 ORDER BY id ASC LIMIT 1')
    ).fetchone()
    rules = {}
    if sdr:
        for row in conn.execute(
            sa.text(
                'SELECT product_id, commission_type, general_customer_amount '
                'FROM commission_rules WHERE sdr_id = :sdr_id AND is_active = 1'
            ),
            {'sdr_id': sdr[0]},
        ):
            rules[row[0]] = row

    existing = {
        row[0]: row[1]
        for row in conn.execute(
            sa.text('SELECT product_id, amount FROM influencer_product_rates')
        )
    }
    products = conn.execute(sa.text('SELECT id FROM products')).fetchall()
    for (product_id,) in products:
        rule = rules.get(product_id)
        commission_type = rule[1] if rule and rule[1] in ('per_item', 'per_weight') else 'per_item'
        amount = rule[2] if rule and rule[2] is not None else 0
        if amount < 0:
            amount = 0
        if product_id in existing:
            if existing[product_id] is not None and float(existing[product_id]) != 0:
                continue
            if not rule:
                continue
            conn.execute(
                sa.text(
                    'UPDATE influencer_product_rates '
                    'SET commission_type = :commission_type, amount = :amount, updated_at = :updated_at '
                    'WHERE product_id = :product_id'
                ),
                {
                    'updated_at': now,
                    'product_id': product_id,
                    'commission_type': commission_type,
                    'amount': amount,
                },
            )
            continue
        conn.execute(
            sa.text(
                'INSERT INTO influencer_product_rates '
                '(created_at, updated_at, product_id, commission_type, amount) '
                'VALUES (:created_at, :updated_at, :product_id, :commission_type, :amount)'
            ),
            {
                'created_at': now,
                'updated_at': now,
                'product_id': product_id,
                'commission_type': commission_type,
                'amount': amount,
            },
        )


def downgrade():
    pass
