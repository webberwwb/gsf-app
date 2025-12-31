"""Add images array to products

Revision ID: add_product_images
Revises: add_product_supplier
Create Date: 2024-12-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_product_images'
down_revision = 'add_wechat_column'
branch_labels = None
depends_on = None


def upgrade():
    # Add images column as JSON array
    op.add_column('products', sa.Column('images', sa.JSON(), nullable=True))
    
    # Migrate existing single image to images array
    # This is done via SQL update
    connection = op.get_bind()
    # Check database type and use appropriate JSON function
    if connection.dialect.name == 'postgresql':
        connection.execute(sa.text("""
            UPDATE products 
            SET images = json_build_array(image) 
            WHERE image IS NOT NULL AND images IS NULL
        """))
    elif connection.dialect.name == 'mysql':
        # MySQL JSON_ARRAY function
        connection.execute(sa.text("""
            UPDATE products 
            SET images = JSON_ARRAY(image) 
            WHERE image IS NOT NULL AND images IS NULL
        """))
    else:
        # SQLite JSON_ARRAY function
        connection.execute(sa.text("""
            UPDATE products 
            SET images = json_array(image) 
            WHERE image IS NOT NULL AND images IS NULL
        """))


def downgrade():
    # Extract first image from images array back to image column
    connection = op.get_bind()
    if connection.dialect.name == 'postgresql':
        connection.execute(sa.text("""
            UPDATE products 
            SET image = images->>0 
            WHERE images IS NOT NULL AND json_array_length(images) > 0
        """))
    elif connection.dialect.name == 'mysql':
        # MySQL JSON_EXTRACT function
        connection.execute(sa.text("""
            UPDATE products 
            SET image = JSON_UNQUOTE(JSON_EXTRACT(images, '$[0]')) 
            WHERE images IS NOT NULL AND JSON_LENGTH(images) > 0
        """))
    else:
        # SQLite JSON_EXTRACT function
        connection.execute(sa.text("""
            UPDATE products 
            SET image = json_extract(images, '$[0]') 
            WHERE images IS NOT NULL
        """))
    
    # Remove images column
    op.drop_column('products', 'images')

