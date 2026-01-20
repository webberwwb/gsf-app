"""add_delivery_fee_config

Revision ID: add_delivery_fee_config
Revises: 0759a3792329
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Numeric


# revision identifiers, used by Alembic.
revision = 'add_delivery_fee_config'
down_revision = '185ab432aa9d'
branch_labels = None
depends_on = None


def upgrade():
    # Create delivery_fee_configs table
    op.create_table('delivery_fee_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('base_fee', Numeric(10, 2), nullable=False, server_default='7.99'),
        sa.Column('threshold_1_amount', Numeric(10, 2), nullable=False, server_default='58.00'),
        sa.Column('threshold_1_fee', Numeric(10, 2), nullable=False, server_default='5.99'),
        sa.Column('threshold_2_amount', Numeric(10, 2), nullable=False, server_default='128.00'),
        sa.Column('threshold_2_fee', Numeric(10, 2), nullable=False, server_default='3.99'),
        sa.Column('threshold_3_amount', Numeric(10, 2), nullable=False, server_default='150.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Insert default configuration
    op.execute("""
        INSERT INTO delivery_fee_configs 
        (created_at, updated_at, base_fee, threshold_1_amount, threshold_1_fee, 
         threshold_2_amount, threshold_2_fee, threshold_3_amount, is_active)
        VALUES 
        (NOW(), NOW(), 7.99, 58.00, 5.99, 128.00, 3.99, 150.00, 1)
    """)


def downgrade():
    op.drop_table('delivery_fee_configs')
