"""add_sort_order_to_products

Revision ID: add_sort_order_to_products
Revises: e551ec893917
Create Date: 2026-01-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_sort_order_to_products'
down_revision = 'e551ec893917'
branch_labels = None
depends_on = None


def upgrade():
    # Add sort_order column to products table
    # Default is 0, lower numbers appear first
    op.add_column('products', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
    # Create index for better query performance
    op.create_index('ix_products_sort_order', 'products', ['sort_order'])


def downgrade():
    # Remove index
    op.drop_index('ix_products_sort_order', table_name='products')
    # Remove sort_order column
    op.drop_column('products', 'sort_order')
