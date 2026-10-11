"""Mark a driver's group-deal settlement as paid.

Revision ID: add_fulfillment_settlements
Revises: add_cash_collected_on_delivery
Create Date: 2026-10-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'add_fulfillment_settlements'
down_revision = 'add_cash_collected_on_delivery'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'fulfillment_settlements' in inspector.get_table_names():
        return
    op.create_table(
        'fulfillment_settlements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_deal_id', sa.Integer(), nullable=True),
        sa.Column('settled_at', sa.DateTime(), nullable=False),
        sa.Column('settled_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['group_deal_id'], ['group_deals.id']),
        sa.ForeignKeyConstraint(['settled_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fulfillment_settlements_user_id', 'fulfillment_settlements', ['user_id'])
    op.create_index('ix_fulfillment_settlements_group_deal_id', 'fulfillment_settlements', ['group_deal_id'])
    op.create_unique_constraint(
        'uq_fulfillment_settlement_user_deal',
        'fulfillment_settlements',
        ['user_id', 'group_deal_id'],
    )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'fulfillment_settlements' not in inspector.get_table_names():
        return
    op.drop_index('ix_fulfillment_settlements_group_deal_id', table_name='fulfillment_settlements')
    op.drop_index('ix_fulfillment_settlements_user_id', table_name='fulfillment_settlements')
    op.drop_table('fulfillment_settlements')
