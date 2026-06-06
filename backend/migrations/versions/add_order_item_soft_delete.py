"""Add soft delete to order_items

Revision ID: add_order_item_soft_delete
Revises: add_cannot_fulfill
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_order_item_soft_delete'
down_revision = 'add_cannot_fulfill'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_order_items_deleted_at'),
            ['deleted_at'],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_order_items_deleted_at'))
        batch_op.drop_column('deleted_at')
