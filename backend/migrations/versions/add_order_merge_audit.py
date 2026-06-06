"""Order merge lineage and audit events

Revision ID: add_order_merge_audit
Revises: add_order_item_soft_delete
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_order_merge_audit'
down_revision = 'add_order_item_soft_delete'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('merged_into_order_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('merged_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            'fk_orders_merged_into_order_id',
            'orders',
            ['merged_into_order_id'],
            ['id'],
        )
        batch_op.create_index(
            batch_op.f('ix_orders_merged_into_order_id'),
            ['merged_into_order_id'],
            unique=False,
        )

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_order_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('source_item_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_order_items_source_order_id',
            'orders',
            ['source_order_id'],
            ['id'],
        )
        batch_op.create_foreign_key(
            'fk_order_items_source_item_id',
            'order_items',
            ['source_item_id'],
            ['id'],
        )
        batch_op.create_index(
            batch_op.f('ix_order_items_source_order_id'),
            ['source_order_id'],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f('ix_order_items_source_item_id'),
            ['source_item_id'],
            unique=False,
        )

    op.create_table(
        'order_audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('order_audit_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_order_audit_events_order_id'), ['order_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_audit_events_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_order_audit_events_actor_user_id'), ['actor_user_id'], unique=False)


def downgrade():
    op.drop_table('order_audit_events')
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_order_items_source_item_id'))
        batch_op.drop_index(batch_op.f('ix_order_items_source_order_id'))
        batch_op.drop_constraint('fk_order_items_source_item_id', type_='foreignkey')
        batch_op.drop_constraint('fk_order_items_source_order_id', type_='foreignkey')
        batch_op.drop_column('source_item_id')
        batch_op.drop_column('source_order_id')
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_orders_merged_into_order_id'))
        batch_op.drop_constraint('fk_orders_merged_into_order_id', type_='foreignkey')
        batch_op.drop_column('merged_at')
        batch_op.drop_column('merged_into_order_id')
