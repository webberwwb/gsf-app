"""add customer_feedback table

Revision ID: add_customer_feedback
Revises: migrate_delivery_fee_to_tiers
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_customer_feedback'
down_revision = 'migrate_delivery_fee_to_tiers'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'customer_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('context', sa.String(length=64), nullable=True),
        sa.Column('outcome', sa.String(length=32), nullable=False, server_default='未联系'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_customer_feedback_context'),
        'customer_feedback',
        ['context'],
        unique=False,
    )
    op.create_index(
        op.f('ix_customer_feedback_order_id'),
        'customer_feedback',
        ['order_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_customer_feedback_user_id'),
        'customer_feedback',
        ['user_id'],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f('ix_customer_feedback_user_id'), table_name='customer_feedback')
    op.drop_index(op.f('ix_customer_feedback_order_id'), table_name='customer_feedback')
    op.drop_index(op.f('ix_customer_feedback_context'), table_name='customer_feedback')
    op.drop_table('customer_feedback')
