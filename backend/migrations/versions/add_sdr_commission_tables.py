"""add_sdr_commission_tables

Revision ID: add_sdr_commission
Revises: add_delivery_fee_config
Create Date: 2026-01-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_sdr_commission'
down_revision = 'add_delivery_fee_config'
branch_labels = None
depends_on = None


def upgrade():
    # Create sdrs table
    op.create_table('sdrs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_identifier', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('sdrs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_sdrs_source_identifier'), ['source_identifier'], unique=True)

    # Create commission_rules table
    op.create_table('commission_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('sdr_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('own_customer_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('general_customer_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['sdr_id'], ['sdrs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sdr_id', 'product_id', name='uq_sdr_product')
    )
    with op.batch_alter_table('commission_rules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_commission_rules_product_id'), ['product_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_commission_rules_sdr_id'), ['sdr_id'], unique=False)

    # Create commission_records table
    op.create_table('commission_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('group_deal_id', sa.Integer(), nullable=False),
        sa.Column('sdr_id', sa.Integer(), nullable=False),
        sa.Column('total_commission', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('own_customer_commission', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('general_customer_commission', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=False),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('payment_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['group_deal_id'], ['group_deals.id'], ),
        sa.ForeignKeyConstraint(['sdr_id'], ['sdrs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_deal_id', 'sdr_id', name='uq_groupdeal_sdr')
    )
    with op.batch_alter_table('commission_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_commission_records_group_deal_id'), ['group_deal_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_commission_records_sdr_id'), ['sdr_id'], unique=False)


def downgrade():
    # Drop commission_records table
    with op.batch_alter_table('commission_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_commission_records_sdr_id'))
        batch_op.drop_index(batch_op.f('ix_commission_records_group_deal_id'))
    op.drop_table('commission_records')

    # Drop commission_rules table
    with op.batch_alter_table('commission_rules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_commission_rules_sdr_id'))
        batch_op.drop_index(batch_op.f('ix_commission_rules_product_id'))
    op.drop_table('commission_rules')

    # Drop sdrs table
    with op.batch_alter_table('sdrs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_sdrs_source_identifier'))
    op.drop_table('sdrs')
