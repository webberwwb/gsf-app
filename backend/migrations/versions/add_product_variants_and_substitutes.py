"""add_product_variants_and_substitutes

Revision ID: add_product_variants_substitutes
Revises: add_store_credit_referrals
Create Date: 2026-05-19

Adds product variants, embedded substitute config, and order item variant/substitute fields.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'add_product_variants_substitutes'
down_revision = 'add_store_credit_referrals'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'product_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('price_delta', mysql.NUMERIC(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_product_variants_product_id'), ['product_id'], unique=False)

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('substitute_enabled', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('substitute_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('substitute_description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('substitute_images', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('substitute_price', mysql.NUMERIC(precision=10, scale=2), nullable=True))

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('variant_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('variant_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('variant_price_delta', mysql.NUMERIC(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('accept_substitute', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('is_unavailable', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.create_foreign_key(
            'fk_order_items_variant_id',
            'product_variants',
            ['variant_id'],
            ['id'],
        )
        batch_op.create_index(batch_op.f('ix_order_items_variant_id'), ['variant_id'], unique=False)


def downgrade():
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_order_items_variant_id'))
        batch_op.drop_constraint('fk_order_items_variant_id', type_='foreignkey')
        batch_op.drop_column('is_unavailable')
        batch_op.drop_column('accept_substitute')
        batch_op.drop_column('variant_price_delta')
        batch_op.drop_column('variant_name')
        batch_op.drop_column('variant_id')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('substitute_price')
        batch_op.drop_column('substitute_images')
        batch_op.drop_column('substitute_description')
        batch_op.drop_column('substitute_name')
        batch_op.drop_column('substitute_enabled')

    with op.batch_alter_table('product_variants', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_product_variants_product_id'))
    op.drop_table('product_variants')
