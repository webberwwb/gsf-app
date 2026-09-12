"""deal_stock_limit is a cap, not remaining

Revision ID: deal_stock_limit_is_cap
Revises: add_delivery_consent
Create Date: 2026-09-12

Older code decremented deal_stock_limit on each order. Convert stored
remaining back to the original cap: remaining + live reserved qty.
"""
from alembic import op
from sqlalchemy import text


revision = 'deal_stock_limit_is_cap'
down_revision = 'add_delivery_consent'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(text("""
        UPDATE group_deal_products gdp
        SET deal_stock_limit = deal_stock_limit + (
            SELECT COALESCE(SUM(oi.quantity), 0)
            FROM order_items oi
            INNER JOIN orders o ON o.id = oi.order_id
            WHERE o.group_deal_id = gdp.group_deal_id
              AND oi.product_id = gdp.product_id
              AND o.deleted_at IS NULL
              AND oi.deleted_at IS NULL
              AND o.status <> 'cancelled'
        )
        WHERE gdp.deal_stock_limit IS NOT NULL
    """))


def downgrade():
    op.execute(text("""
        UPDATE group_deal_products gdp
        SET deal_stock_limit = GREATEST(0, deal_stock_limit - (
            SELECT COALESCE(SUM(oi.quantity), 0)
            FROM order_items oi
            INNER JOIN orders o ON o.id = oi.order_id
            WHERE o.group_deal_id = gdp.group_deal_id
              AND oi.product_id = gdp.product_id
              AND o.deleted_at IS NULL
              AND oi.deleted_at IS NULL
              AND o.status <> 'cancelled'
        ))
        WHERE gdp.deal_stock_limit IS NOT NULL
    """))
