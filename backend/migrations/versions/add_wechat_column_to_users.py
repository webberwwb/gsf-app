"""Add wechat column to users table

Revision ID: add_wechat_column
Revises: add_group_deal_soft_delete
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_wechat_column'
down_revision = 'add_group_deal_soft_delete'
branch_labels = None
depends_on = None


def upgrade():
    # Add wechat column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('wechat', sa.String(length=255), nullable=True))


def downgrade():
    # Remove wechat column from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('wechat')

