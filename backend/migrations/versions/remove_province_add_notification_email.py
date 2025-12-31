"""remove_province_add_notification_email

Revision ID: remove_province_add_email
Revises: add_shipping_fee_to_orders
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_province_add_email'
down_revision = 'add_shipping_fee_to_orders'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before modifying
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('addresses')]
    
    # Remove province column from addresses table if it exists
    if 'province' in columns:
        op.drop_column('addresses', 'province')
    
    # Add notification_email column to addresses table if it doesn't exist
    if 'notification_email' not in columns:
        op.add_column('addresses', sa.Column('notification_email', sa.String(length=255), nullable=True))


def downgrade():
    # Remove notification_email column
    op.drop_column('addresses', 'notification_email')
    
    # Add back province column (with default value for existing rows)
    op.add_column('addresses', sa.Column('province', sa.String(length=100), nullable=False, server_default='Ontario'))

