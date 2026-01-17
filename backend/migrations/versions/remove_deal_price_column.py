"""remove_deal_price_column

Revision ID: remove_deal_price_column
Revises: remove_legacy_price_fields
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'remove_deal_price_column'
down_revision = 'remove_legacy_price_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Remove deal_price column from group_deal_products table
    with op.batch_alter_table('group_deal_products', schema=None) as batch_op:
        batch_op.drop_column('deal_price')


def downgrade():
    # Restore deal_price column if needed
    with op.batch_alter_table('group_deal_products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deal_price', mysql.NUMERIC(precision=10, scale=2), nullable=True))
