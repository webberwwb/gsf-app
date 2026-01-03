"""add_group_deal_soft_delete

Revision ID: add_group_deal_soft_delete
Revises: remove_province_add_email
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_group_deal_soft_delete'
down_revision = 'remove_province_add_email'
branch_labels = None
depends_on = None


def upgrade():
    # Add deleted_at column to group_deals table for soft delete
    with op.batch_alter_table('group_deals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_group_deals_deleted_at', ['deleted_at'])


def downgrade():
    # Remove deleted_at column and index
    with op.batch_alter_table('group_deals', schema=None) as batch_op:
        batch_op.drop_index('ix_group_deals_deleted_at')
        batch_op.drop_column('deleted_at')




