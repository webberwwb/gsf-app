"""add_pickup_location_to_orders

Revision ID: d8ff6cd6b1f6
Revises: add_final_weight_to_order_items
Create Date: 2025-12-27 16:46:19.920952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8ff6cd6b1f6'
down_revision = 'add_final_weight_to_order_items'
branch_labels = None
depends_on = None


def upgrade():
    # Add pickup_location column to orders table
    op.add_column('orders', sa.Column('pickup_location', sa.String(length=100), nullable=True))
    
    # Migrate existing pickup_location data from notes field
    # Extract pickup_location from notes and update the new column
    op.execute("""
        UPDATE orders 
        SET pickup_location = SUBSTRING_INDEX(
            SUBSTRING_INDEX(notes, 'Pickup Location:', -1), 
            '\n', 
            1
        )
        WHERE notes LIKE '%Pickup Location:%' 
        AND pickup_location IS NULL
    """)


def downgrade():
    # Remove pickup_location column
    op.drop_column('orders', 'pickup_location')
