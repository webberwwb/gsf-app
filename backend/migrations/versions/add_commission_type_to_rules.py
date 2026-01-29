"""add_commission_type_to_rules

Revision ID: add_commission_type
Revises: add_manual_adjustment
Create Date: 2026-01-29 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_commission_type'
down_revision = 'add_manual_adjustment'
branch_labels = None
depends_on = None


def upgrade():
    # Add commission_type column to commission_rules table
    with op.batch_alter_table('commission_rules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('commission_type', sa.String(length=20), nullable=False, server_default='per_item'))


def downgrade():
    # Remove commission_type column from commission_rules table
    with op.batch_alter_table('commission_rules', schema=None) as batch_op:
        batch_op.drop_column('commission_type')
