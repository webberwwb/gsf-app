"""migrate_delivery_fee_to_tiers

Revision ID: migrate_delivery_fee_to_tiers
Revises: add_delivery_fee_config
Create Date: 2026-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'migrate_delivery_fee_to_tiers'
down_revision = 'add_sort_order_to_products'
branch_labels = None
depends_on = None


def upgrade():
    # First, add the new tiers column as nullable
    op.add_column('delivery_fee_configs', 
        sa.Column('tiers', JSON, nullable=True)
    )
    
    # Migrate existing data: Convert old structure to new tiers format
    # This uses raw SQL to read old columns and populate the new tiers column
    connection = op.get_bind()
    
    # Get all existing configs
    result = connection.execute(sa.text("""
        SELECT id, base_fee, threshold_1_amount, threshold_1_fee, 
               threshold_2_amount, threshold_2_fee, threshold_3_amount
        FROM delivery_fee_configs
    """))
    
    # For each config, create tiers array and update
    for row in result:
        tiers = [
            {"threshold": 0, "fee": float(row.base_fee)},
            {"threshold": float(row.threshold_1_amount), "fee": float(row.threshold_1_fee)},
            {"threshold": float(row.threshold_2_amount), "fee": float(row.threshold_2_fee)},
            {"threshold": float(row.threshold_3_amount), "fee": 0}
        ]
        
        # Update with tiers data
        import json
        connection.execute(
            sa.text("UPDATE delivery_fee_configs SET tiers = :tiers WHERE id = :id"),
            {"tiers": json.dumps(tiers), "id": row.id}
        )
    
    # Now make tiers NOT NULL since all rows have been updated
    # For MySQL, we need to specify the type when altering
    from sqlalchemy.dialects import mysql
    op.alter_column('delivery_fee_configs', 'tiers',
               existing_type=mysql.JSON(),
               type_=mysql.JSON(),
               nullable=False)
    
    # Drop old columns
    op.drop_column('delivery_fee_configs', 'base_fee')
    op.drop_column('delivery_fee_configs', 'threshold_1_amount')
    op.drop_column('delivery_fee_configs', 'threshold_1_fee')
    op.drop_column('delivery_fee_configs', 'threshold_2_amount')
    op.drop_column('delivery_fee_configs', 'threshold_2_fee')
    op.drop_column('delivery_fee_configs', 'threshold_3_amount')


def downgrade():
    # Add back the old columns
    from sqlalchemy import Numeric
    
    op.add_column('delivery_fee_configs',
        sa.Column('base_fee', Numeric(10, 2), nullable=True)
    )
    op.add_column('delivery_fee_configs',
        sa.Column('threshold_1_amount', Numeric(10, 2), nullable=True)
    )
    op.add_column('delivery_fee_configs',
        sa.Column('threshold_1_fee', Numeric(10, 2), nullable=True)
    )
    op.add_column('delivery_fee_configs',
        sa.Column('threshold_2_amount', Numeric(10, 2), nullable=True)
    )
    op.add_column('delivery_fee_configs',
        sa.Column('threshold_2_fee', Numeric(10, 2), nullable=True)
    )
    op.add_column('delivery_fee_configs',
        sa.Column('threshold_3_amount', Numeric(10, 2), nullable=True)
    )
    
    # Migrate data back from tiers to old structure
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id, tiers FROM delivery_fee_configs"))
    
    import json
    for row in result:
        tiers = json.loads(row.tiers) if isinstance(row.tiers, str) else row.tiers
        
        # Assume old structure: base fee (threshold 0) + 3 thresholds
        # If there are fewer tiers, use defaults
        base_fee = 7.99
        threshold_1_amount = 58.00
        threshold_1_fee = 5.99
        threshold_2_amount = 128.00
        threshold_2_fee = 3.99
        threshold_3_amount = 150.00
        
        if len(tiers) >= 1 and tiers[0].get('threshold') == 0:
            base_fee = tiers[0].get('fee', 7.99)
        if len(tiers) >= 2:
            threshold_1_amount = tiers[1].get('threshold', 58.00)
            threshold_1_fee = tiers[1].get('fee', 5.99)
        if len(tiers) >= 3:
            threshold_2_amount = tiers[2].get('threshold', 128.00)
            threshold_2_fee = tiers[2].get('fee', 3.99)
        if len(tiers) >= 4:
            threshold_3_amount = tiers[3].get('threshold', 150.00)
        
        connection.execute(
            sa.text("""
                UPDATE delivery_fee_configs 
                SET base_fee = :base_fee,
                    threshold_1_amount = :t1_amt, threshold_1_fee = :t1_fee,
                    threshold_2_amount = :t2_amt, threshold_2_fee = :t2_fee,
                    threshold_3_amount = :t3_amt
                WHERE id = :id
            """),
            {
                "base_fee": base_fee,
                "t1_amt": threshold_1_amount, "t1_fee": threshold_1_fee,
                "t2_amt": threshold_2_amount, "t2_fee": threshold_2_fee,
                "t3_amt": threshold_3_amount,
                "id": row.id
            }
        )
    
    # Make old columns NOT NULL with defaults  
    # For MySQL, we need to specify type when altering
    from sqlalchemy.dialects import mysql
    op.alter_column('delivery_fee_configs', 'base_fee', 
                   existing_type=mysql.DECIMAL(10, 2),
                   type_=mysql.DECIMAL(10, 2),
                   nullable=False, 
                   server_default='7.99')
    op.alter_column('delivery_fee_configs', 'threshold_1_amount',
                   existing_type=mysql.DECIMAL(10, 2),
                   type_=mysql.DECIMAL(10, 2),
                   nullable=False, 
                   server_default='58.00')
    op.alter_column('delivery_fee_configs', 'threshold_1_fee',
                   existing_type=mysql.DECIMAL(10, 2),
                   type_=mysql.DECIMAL(10, 2),
                   nullable=False, 
                   server_default='5.99')
    op.alter_column('delivery_fee_configs', 'threshold_2_amount',
                   existing_type=mysql.DECIMAL(10, 2),
                   type_=mysql.DECIMAL(10, 2),
                   nullable=False, 
                   server_default='128.00')
    op.alter_column('delivery_fee_configs', 'threshold_2_fee',
                   existing_type=mysql.DECIMAL(10, 2),
                   type_=mysql.DECIMAL(10, 2),
                   nullable=False, 
                   server_default='3.99')
    op.alter_column('delivery_fee_configs', 'threshold_3_amount',
                   existing_type=mysql.DECIMAL(10, 2),
                   type_=mysql.DECIMAL(10, 2),
                   nullable=False, 
                   server_default='150.00')
    
    # Drop tiers column
    op.drop_column('delivery_fee_configs', 'tiers')
