"""add_shipping_fee_to_orders

Revision ID: add_shipping_fee_to_orders
Revises: d8ff6cd6b1f6
Create Date: 2025-12-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric


# revision identifiers, used by Alembic.
revision = 'add_shipping_fee_to_orders'
down_revision = 'd8ff6cd6b1f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add shipping_fee column to orders table
    op.add_column('orders', sa.Column('shipping_fee', Numeric(10, 2), nullable=False, server_default='0.00'))


def downgrade():
    # Remove shipping_fee column
    op.drop_column('orders', 'shipping_fee')




