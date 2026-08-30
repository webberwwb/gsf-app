"""add_deal_product_discount

Revision ID: add_deal_product_discount
Revises: add_variant_sale_price
Create Date: 2026-08-25

Sale/discount is per group-deal product, not a catalog-wide product flag.
Copies existing products.is_discount onto group_deal_products, then clears
the product-level flag.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = 'add_deal_product_discount'
down_revision = 'add_variant_sale_price'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('group_deal_products', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'is_discount',
            sa.Boolean(),
            nullable=False,
            server_default='0',
        ))

    conn = op.get_bind()
    conn.execute(text("""
        UPDATE group_deal_products gdp
        INNER JOIN products p ON p.id = gdp.product_id
        SET gdp.is_discount = 1
        WHERE p.is_discount = 1
    """))
    conn.execute(text("UPDATE products SET is_discount = 0"))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE products p
        INNER JOIN (
            SELECT product_id
            FROM group_deal_products
            WHERE is_discount = 1
            GROUP BY product_id
        ) d ON d.product_id = p.id
        SET p.is_discount = 1
    """))
    with op.batch_alter_table('group_deal_products', schema=None) as batch_op:
        batch_op.drop_column('is_discount')
