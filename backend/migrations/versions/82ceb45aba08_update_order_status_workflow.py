"""update_order_status_workflow

Revision ID: 82ceb45aba08
Revises: 8a6d323dde12
Create Date: 2025-12-26 10:45:09.693054

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82ceb45aba08'
down_revision = '8a6d323dde12'
branch_labels = None
depends_on = None


def upgrade():
    # Check if delivery_method column exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('orders')]
    
    if 'delivery_method' not in columns:
        # Add delivery_method column
        op.add_column('orders', sa.Column('delivery_method', sa.String(50), nullable=True))
        
        # Update all existing orders to have pickup as default delivery method
        op.execute("UPDATE orders SET delivery_method = 'pickup' WHERE delivery_method IS NULL")
        
        # Now make it non-nullable (MySQL requires existing_type)
        op.alter_column('orders', 'delivery_method', 
                        existing_type=sa.String(50), 
                        nullable=False)
    
    # Update status values from old to new
    # pending -> submitted (newly created orders)
    op.execute("UPDATE orders SET status = 'submitted' WHERE status = 'pending'")
    
    # confirmed -> confirmed (already correct)
    # processing -> preparing (配货中)
    op.execute("UPDATE orders SET status = 'preparing' WHERE status = 'processing'")
    
    # completed -> completed (already correct)
    # cancelled -> cancelled (already correct)
    
    # Update payment_status from old values to new
    # pending -> unpaid
    op.execute("UPDATE orders SET payment_status = 'unpaid' WHERE payment_status = 'pending'")
    
    # paid -> paid (already correct)
    # failed, refunded -> keep as is for now (edge cases)
    
    # Add status column to group_deals table if it doesn't exist
    # Check if column exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('group_deals')]
    
    if 'status' not in columns:
        op.add_column('group_deals', sa.Column('status', sa.String(50), nullable=True))
        # Set default status for existing group deals
        op.execute("UPDATE group_deals SET status = 'active' WHERE status IS NULL")
        op.alter_column('group_deals', 'status',
                       existing_type=sa.String(50),
                       nullable=False)


def downgrade():
    # Reverse status changes
    op.execute("UPDATE orders SET status = 'pending' WHERE status = 'submitted'")
    op.execute("UPDATE orders SET status = 'processing' WHERE status = 'preparing'")
    
    # Reverse payment_status changes
    op.execute("UPDATE orders SET payment_status = 'pending' WHERE payment_status = 'unpaid'")
    
    # Remove delivery_method column
    op.drop_column('orders', 'delivery_method')
    
    # Check and remove status column from group_deals if it exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('group_deals')]
    
    if 'status' in columns:
        op.drop_column('group_deals', 'status')
