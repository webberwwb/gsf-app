"""add_variant_sale_price

Revision ID: add_variant_sale_price
Revises: add_discount_variant_pricing
Create Date: 2026-08-24

Absolute sale price on a variant when the product is on sale and variants
do not share a price. Additive; existing rows stay null.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_variant_sale_price'
down_revision = 'add_discount_variant_pricing'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'sale_price',
            mysql.NUMERIC(precision=10, scale=2),
            nullable=True,
        ))


def downgrade():
    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.drop_column('sale_price')
