"""Add user_source column to users table

Revision ID: add_user_source
Revises: 8a6d323dde12
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_user_source'
down_revision = '8a6d323dde12'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_source column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_source', sa.String(length=50), nullable=True, server_default='default'))


def downgrade():
    # Remove user_source column from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('user_source')
