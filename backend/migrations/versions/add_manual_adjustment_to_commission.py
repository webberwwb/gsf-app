"""add_manual_adjustment_to_commission

Revision ID: add_manual_adjustment
Revises: add_sdr_commission
Create Date: 2026-01-29 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_manual_adjustment'
down_revision = 'add_sdr_commission'
branch_labels = None
depends_on = None


def upgrade():
    # Add manual adjustment fields to commission_records table
    with op.batch_alter_table('commission_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manual_adjustment', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('adjustment_notes', sa.Text(), nullable=True))


def downgrade():
    # Remove manual adjustment fields from commission_records table
    with op.batch_alter_table('commission_records', schema=None) as batch_op:
        batch_op.drop_column('adjustment_notes')
        batch_op.drop_column('manual_adjustment')
