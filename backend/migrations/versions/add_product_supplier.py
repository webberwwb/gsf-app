"""Add supplier to products

Revision ID: add_product_supplier
Revises: add_product_pricing_types
Create Date: 2024-12-21 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_product_supplier'
down_revision = 'add_product_pricing_types'
branch_labels = None
depends_on = None


def upgrade():
    # Add supplier_id foreign key column
    op.add_column('products', sa.Column('supplier_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_products_supplier_id'), 'products', ['supplier_id'], unique=False)
    op.create_foreign_key('fk_products_supplier_id', 'products', 'suppliers', ['supplier_id'], ['id'])


def downgrade():
    # Remove foreign key and column
    op.drop_constraint('fk_products_supplier_id', 'products', type_='foreignkey')
    op.drop_index(op.f('ix_products_supplier_id'), table_name='products')
    op.drop_column('products', 'supplier_id')


