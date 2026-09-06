"""add_group_deal_online_payment

Revision ID: add_group_deal_online_payment
Revises: add_stripe_payment_columns
Create Date: 2026-09-05

Per-deal Stripe/card checkout. Existing deals stay on cash / e-transfer.
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_group_deal_online_payment'
down_revision = 'add_stripe_payment_columns'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('group_deals', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'online_payment_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ))


def downgrade():
    with op.batch_alter_table('group_deals', schema=None) as batch_op:
        batch_op.drop_column('online_payment_enabled')
