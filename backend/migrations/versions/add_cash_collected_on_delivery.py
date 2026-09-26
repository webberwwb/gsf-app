"""Store cash the driver confirmed on delivery. Do not backfill paid cash.

Revision ID: add_cash_collected_on_delivery
Revises: add_coords_and_rings
Create Date: 2026-09-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'add_cash_collected_on_delivery'
down_revision = 'add_coords_and_rings'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    order_cols = {col['name'] for col in inspector.get_columns('orders')}
    if 'cash_collected_on_delivery' not in order_cols:
        op.add_column(
            'orders',
            sa.Column('cash_collected_on_delivery', sa.Numeric(10, 2), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    order_cols = {col['name'] for col in inspector.get_columns('orders')}
    if 'cash_collected_on_delivery' in order_cols:
        op.drop_column('orders', 'cash_collected_on_delivery')
