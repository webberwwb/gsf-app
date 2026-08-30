"""add_product_discount_and_variant_pricing

Revision ID: add_discount_variant_pricing
Revises: add_commission_excluded_users
Create Date: 2026-08-24

Additive product flags and per-variant absolute price / quantity breaks.
Does not rewrite existing products, variants, or orders.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_discount_variant_pricing'
down_revision = 'add_commission_excluded_users'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'variants_share_price',
            sa.Boolean(),
            nullable=False,
            server_default='1',
        ))
        batch_op.add_column(sa.Column(
            'is_discount',
            sa.Boolean(),
            nullable=False,
            server_default='0',
        ))

    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'price',
            mysql.NUMERIC(precision=10, scale=2),
            nullable=True,
        ))
        batch_op.add_column(sa.Column(
            'quantity_breaks',
            sa.JSON(),
            nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.drop_column('quantity_breaks')
        batch_op.drop_column('price')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('is_discount')
        batch_op.drop_column('variants_share_price')
