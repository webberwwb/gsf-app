"""Hide deleted products from the catalog without turning them 下架.

Revision ID: add_product_deleted_at
Revises: add_fulfillment_settlements
Create Date: 2026-10-10
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_product_deleted_at'
down_revision = 'add_fulfillment_settlements'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_products_deleted_at', ['deleted_at'])


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index('ix_products_deleted_at')
        batch_op.drop_column('deleted_at')
