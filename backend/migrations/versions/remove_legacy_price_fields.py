"""remove_legacy_price_fields

Revision ID: remove_legacy_price_fields
Revises: 0759a3792329
Create Date: 2025-12-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'remove_legacy_price_fields'
down_revision = '0759a3792329'
branch_labels = None
depends_on = None


def upgrade():
    # Remove original_price and sale_price columns from products table
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('original_price')
        batch_op.drop_column('sale_price')


def downgrade():
    # Restore original_price and sale_price columns if needed
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sale_price', mysql.NUMERIC(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('original_price', mysql.NUMERIC(precision=10, scale=2), nullable=True))




