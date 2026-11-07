"""Seed the default wholesale merchant.

Revision ID: seed_default_b_merchant
Revises: add_b_merchants
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from alembic import op
import sqlalchemy as sa


revision = 'seed_default_b_merchant'
down_revision = 'add_b_merchants'
branch_labels = None
depends_on = None

MERCHANT_NAME = '1001280318 Ontario Inc. (Fusion Foodmart)'
PAYMENT_TERMS = (
    'Certified Cheque to 15891779 Canada Inc., Payment due within 1 week / 一周内支付'
)


def upgrade():
    conn = op.get_bind()
    existing = conn.execute(
        sa.text('SELECT id FROM b_merchants WHERE name = :name LIMIT 1'),
        {'name': MERCHANT_NAME},
    ).fetchone()
    if existing:
        return
    now = datetime.now(ZoneInfo('America/New_York')).replace(tzinfo=None)
    conn.execute(
        sa.text(
            'INSERT INTO b_merchants ('
            'created_at, updated_at, name, show_prices, payment_terms, '
            'payment_due_days, is_active'
            ') VALUES ('
            ':created_at, :updated_at, :name, :show_prices, :payment_terms, '
            ':payment_due_days, :is_active'
            ')'
        ),
        {
            'created_at': now,
            'updated_at': now,
            'name': MERCHANT_NAME,
            'show_prices': 1,
            'payment_terms': PAYMENT_TERMS,
            'payment_due_days': 7,
            'is_active': 1,
        },
    )


def downgrade():
    conn = op.get_bind()
    row = conn.execute(
        sa.text('SELECT id FROM b_merchants WHERE name = :name LIMIT 1'),
        {'name': MERCHANT_NAME},
    ).fetchone()
    if not row:
        return
    used = conn.execute(
        sa.text('SELECT id FROM b_deliveries WHERE merchant_id = :id LIMIT 1'),
        {'id': row[0]},
    ).fetchone()
    if used:
        return
    conn.execute(
        sa.text('DELETE FROM b_merchants WHERE id = :id'),
        {'id': row[0]},
    )
