"""add per-product cutting service

Revision ID: add_product_cutting_service
Revises: deal_stock_limit_is_cap
Create Date: 2026-09-12

Product-level 切分 toggle + fee; order_items snapshot the choice and fee.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_product_cutting_service'
down_revision = 'deal_stock_limit_is_cap'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cutting_enabled', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('cutting_fee', mysql.NUMERIC(precision=10, scale=2), nullable=False, server_default='0'))

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cutting', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('cutting_fee', mysql.NUMERIC(precision=10, scale=2), nullable=True))


def downgrade():
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_column('cutting_fee')
        batch_op.drop_column('cutting')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('cutting_fee')
        batch_op.drop_column('cutting_enabled')
