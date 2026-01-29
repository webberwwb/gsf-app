"""add_order_adjustments

Revision ID: add_order_adjustments
Revises: add_commission_type
Create Date: 2026-01-29 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_order_adjustments'
down_revision = 'add_commission_type'
branch_labels = None
depends_on = None


def upgrade():
    # Add adjustment fields to orders table
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('adjustment_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('adjustment_notes', sa.Text(), nullable=True))


def downgrade():
    # Remove adjustment fields from orders table
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('adjustment_notes')
        batch_op.drop_column('adjustment_amount')
