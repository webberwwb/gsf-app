"""add_product_counts_toward_free_shipping

Revision ID: add_product_counts_toward_free_shipping
Revises: add_product_images
Create Date: 2025-12-31 22:59:32.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_prod_free_shipping_flag'
down_revision = 'add_product_images'
branch_labels = None
depends_on = None


def upgrade():
    # Add counts_toward_free_shipping column to products table
    # Default is True (products count toward free shipping threshold by default)
    op.add_column('products', sa.Column('counts_toward_free_shipping', sa.Boolean(), nullable=False, server_default='1'))


def downgrade():
    # Remove counts_toward_free_shipping column
    op.drop_column('products', 'counts_toward_free_shipping')

