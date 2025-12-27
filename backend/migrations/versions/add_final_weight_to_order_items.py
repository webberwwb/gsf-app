"""add_final_weight_to_order_items

Revision ID: add_final_weight_to_order_items
Revises: remove_legacy_price_fields
Create Date: 2025-12-25 12:00:00.000000

Adds final_weight field to order_items table for weight-based products
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_final_weight_to_order_items'
down_revision = 'add_order_soft_delete'
branch_labels = None
depends_on = None


def upgrade():
    # Add final_weight to order_items table
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('final_weight', mysql.NUMERIC(precision=10, scale=3), nullable=True))


def downgrade():
    # Remove final_weight from order_items table
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_column('final_weight')

