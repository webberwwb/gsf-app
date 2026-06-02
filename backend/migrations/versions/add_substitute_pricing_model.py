"""add_substitute_pricing_model

Revision ID: add_substitute_pricing_model
Revises: add_product_variants_substitutes
Create Date: 2026-05-19

Substitute uses same pricing model as product (type + JSON data), not only flat price.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'add_substitute_pricing_model'
down_revision = 'add_product_variants_substitutes'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('substitute_pricing_type', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('substitute_pricing_data', sa.JSON(), nullable=True))

    # Migrate legacy substitute_price -> per_item pricing_data
    op.execute("""
        UPDATE products
        SET substitute_pricing_type = 'per_item',
            substitute_pricing_data = JSON_OBJECT('price', substitute_price)
        WHERE substitute_enabled = 1
          AND substitute_price IS NOT NULL
          AND substitute_pricing_data IS NULL
    """)

    # For enabled substitutes without any pricing, copy from main product pricing
    op.execute("""
        UPDATE products
        SET substitute_pricing_type = pricing_type,
            substitute_pricing_data = pricing_data
        WHERE substitute_enabled = 1
          AND substitute_pricing_data IS NULL
          AND pricing_data IS NOT NULL
    """)


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('substitute_pricing_data')
        batch_op.drop_column('substitute_pricing_type')
