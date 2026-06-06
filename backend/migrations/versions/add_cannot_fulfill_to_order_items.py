"""Add cannot_fulfill flag to order_items

Revision ID: add_cannot_fulfill
Revises: add_substitute_pricing_model
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_cannot_fulfill'
down_revision = 'add_substitute_pricing_model'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('cannot_fulfill', sa.Boolean(), nullable=False, server_default='0')
        )


def downgrade():
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_column('cannot_fulfill')
