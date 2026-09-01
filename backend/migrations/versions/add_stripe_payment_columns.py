"""add_stripe_payment_columns

Revision ID: add_stripe_payment_columns
Revises: add_deal_product_discount
Create Date: 2026-08-30

Store Stripe customer / payment-method IDs and charge status.
Never store PAN, expiry, or CVC.
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_stripe_payment_columns'
down_revision = 'add_deal_product_discount'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_payment_method_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_card_brand', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('stripe_card_last4', sa.String(length=4), nullable=True))
        batch_op.create_index('ix_users_stripe_customer_id', ['stripe_customer_id'])

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_payment_method_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('stripe_charge_status', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('stripe_last_error', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('stripe_payment_link_url', sa.String(length=512), nullable=True))
        batch_op.add_column(sa.Column('stripe_card_brand', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('stripe_card_last4', sa.String(length=4), nullable=True))
        batch_op.add_column(sa.Column('stripe_amount_charged', sa.Numeric(10, 2), nullable=True))


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('stripe_amount_charged')
        batch_op.drop_column('stripe_card_last4')
        batch_op.drop_column('stripe_card_brand')
        batch_op.drop_column('stripe_payment_link_url')
        batch_op.drop_column('stripe_last_error')
        batch_op.drop_column('stripe_charge_status')
        batch_op.drop_column('stripe_payment_method_id')
        batch_op.drop_column('stripe_customer_id')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_stripe_customer_id')
        batch_op.drop_column('stripe_card_last4')
        batch_op.drop_column('stripe_card_brand')
        batch_op.drop_column('stripe_payment_method_id')
        batch_op.drop_column('stripe_customer_id')
