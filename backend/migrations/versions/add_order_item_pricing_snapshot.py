"""Snapshot the paid price schedule on each order line.

Revision ID: add_order_item_pricing_snapshot
Revises: add_recipe_details
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_order_item_pricing_snapshot'
down_revision = 'add_recipe_details'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    json_type = mysql.JSON() if bind.dialect.name == 'mysql' else sa.JSON()
    with op.batch_alter_table('order_items') as batch_op:
        batch_op.add_column(sa.Column('pricing_snapshot', json_type, nullable=True))
        batch_op.add_column(sa.Column('price_choice', sa.String(length=20), nullable=True))

    # Online migrations run inside the Flask app. Backfill stored prices only.
    from alembic import context
    if context.is_offline_mode():
        return
    from utils.order_item_pricing import backfill_pricing_snapshots
    backfill_pricing_snapshots()


def downgrade():
    with op.batch_alter_table('order_items') as batch_op:
        batch_op.drop_column('price_choice')
        batch_op.drop_column('pricing_snapshot')
