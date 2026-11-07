"""Per-flavor stock caps on a group deal product.

Revision ID: add_variant_stock_limits
Revises: add_order_item_pricing_snapshot
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_variant_stock_limits'
down_revision = 'add_order_item_pricing_snapshot'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    json_type = mysql.JSON() if bind.dialect.name == 'mysql' else sa.JSON()
    op.add_column(
        'group_deal_products',
        sa.Column('variant_stock_limits', json_type, nullable=True),
    )


def downgrade():
    op.drop_column('group_deal_products', 'variant_stock_limits')
