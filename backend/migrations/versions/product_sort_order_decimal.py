"""Allow decimal product sort_order values

Revision ID: product_sort_order_decimal
Revises: add_order_merge_audit
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa


revision = 'product_sort_order_decimal'
down_revision = 'add_order_merge_audit'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column(
            'sort_order',
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 4),
            existing_nullable=False,
            existing_server_default='0',
        )


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column(
            'sort_order',
            existing_type=sa.Numeric(12, 4),
            type_=sa.Integer(),
            existing_nullable=False,
            existing_server_default='0',
        )
