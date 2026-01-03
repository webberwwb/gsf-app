"""Add product pricing types

Revision ID: add_product_pricing_types
Revises: add_suppliers_table
Create Date: 2024-12-21 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_product_pricing_types'
down_revision = 'add_suppliers_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add pricing_type column
    op.add_column('products', sa.Column('pricing_type', sa.String(length=20), nullable=False, server_default='per_item'))
    
    # Add pricing_data JSON column
    op.add_column('products', sa.Column('pricing_data', sa.JSON(), nullable=True))
    
    # Make original_price and sale_price nullable (for backward compatibility)
    op.alter_column('products', 'original_price',
                    existing_type=mysql.DECIMAL(precision=10, scale=2),
                    nullable=True)
    op.alter_column('products', 'sale_price',
                    existing_type=mysql.DECIMAL(precision=10, scale=2),
                    nullable=True)
    
    # Migrate existing data: convert sale_price/original_price to pricing_data for per_item type
    op.execute("""
        UPDATE products 
        SET pricing_data = JSON_OBJECT(
            'sale_price', sale_price,
            'original_price', COALESCE(original_price, sale_price)
        )
        WHERE pricing_data IS NULL AND sale_price IS NOT NULL
    """)


def downgrade():
    # Revert pricing_data back to sale_price/original_price for per_item products
    op.execute("""
        UPDATE products 
        SET sale_price = CAST(JSON_EXTRACT(pricing_data, '$.sale_price') AS DECIMAL(10,2)),
            original_price = CAST(JSON_EXTRACT(pricing_data, '$.original_price') AS DECIMAL(10,2))
        WHERE pricing_type = 'per_item' AND pricing_data IS NOT NULL
    """)
    
    # Make original_price and sale_price NOT NULL again
    op.alter_column('products', 'sale_price',
                    existing_type=mysql.DECIMAL(precision=10, scale=2),
                    nullable=False)
    op.alter_column('products', 'original_price',
                    existing_type=mysql.DECIMAL(precision=10, scale=2),
                    nullable=False)
    
    # Remove new columns
    op.drop_column('products', 'pricing_data')
    op.drop_column('products', 'pricing_type')






