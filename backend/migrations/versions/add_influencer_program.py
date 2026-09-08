"""add influencer / 推荐官 program tables

Revision ID: add_influencer_program
Revises: add_group_deal_online_payment
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_influencer_program'
down_revision = 'add_group_deal_online_payment'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'influencer_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('payout_type', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_influencer_profiles_user_id', 'influencer_profiles', ['user_id'])

    op.create_table(
        'influencer_program_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('lead_bonus_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'influencer_product_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('commission_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id'),
    )
    op.create_index('ix_influencer_product_rates_product_id', 'influencer_product_rates', ['product_id'])

    op.create_table(
        'influencer_rate_overrides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('influencer_user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('commission_type', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['influencer_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('influencer_user_id', 'product_id', name='uq_influencer_product_override'),
    )
    op.create_index(
        'ix_influencer_rate_overrides_influencer_user_id',
        'influencer_rate_overrides',
        ['influencer_user_id'],
    )
    op.create_index(
        'ix_influencer_rate_overrides_product_id',
        'influencer_rate_overrides',
        ['product_id'],
    )

    op.create_table(
        'influencer_commission_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('influencer_user_id', sa.Integer(), nullable=False),
        sa.Column('customer_user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payout_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('credit_transaction_id', sa.Integer(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('paid_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['influencer_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['customer_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['credit_transaction_id'], ['credit_transactions.id']),
        sa.ForeignKeyConstraint(['paid_by_admin_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id'),
    )
    op.create_index(
        'ix_influencer_commission_entries_influencer_user_id',
        'influencer_commission_entries',
        ['influencer_user_id'],
    )
    op.create_index(
        'ix_influencer_commission_entries_customer_user_id',
        'influencer_commission_entries',
        ['customer_user_id'],
    )
    op.create_index(
        'ix_influencer_commission_entries_status',
        'influencer_commission_entries',
        ['status'],
    )


def downgrade():
    op.drop_table('influencer_commission_entries')
    op.drop_table('influencer_rate_overrides')
    op.drop_table('influencer_product_rates')
    op.drop_table('influencer_program_configs')
    op.drop_table('influencer_profiles')
