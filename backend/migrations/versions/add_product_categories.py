"""Add product categories

Revision ID: add_product_categories
Revises: 20260402164045
Create Date: 2026-04-25 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_product_categories'
down_revision = '20260402164045'
branch_labels = None
depends_on = None


def upgrade():
    # Create product_categories table
    op.create_table('product_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Add indexes
    op.create_index(op.f('ix_product_categories_name'), 'product_categories', ['name'], unique=False)
    op.create_index(op.f('ix_product_categories_sort_order'), 'product_categories', ['sort_order'], unique=False)
    
    # Add category_id column to products table
    op.add_column('products', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_foreign_key('fk_products_category_id', 'products', 'product_categories', ['category_id'], ['id'])


def downgrade():
    # Remove foreign key and column from products table
    op.drop_constraint('fk_products_category_id', 'products', type_='foreignkey')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_column('products', 'category_id')
    
    # Drop product_categories table
    op.drop_index(op.f('ix_product_categories_sort_order'), table_name='product_categories')
    op.drop_index(op.f('ix_product_categories_name'), table_name='product_categories')
    op.drop_table('product_categories')
