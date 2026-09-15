"""persist address coords and delivery distance rings

Revision ID: add_coords_and_rings
Revises: add_product_cutting_service
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_coords_and_rings'
down_revision = 'add_product_cutting_service'
branch_labels = None
depends_on = None


def _columns(table):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table)}


def upgrade():
    address_cols = _columns('addresses')
    with op.batch_alter_table('addresses', schema=None) as batch_op:
        if 'latitude' not in address_cols:
            batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        if 'longitude' not in address_cols:
            batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))
        if 'place_id' not in address_cols:
            batch_op.add_column(sa.Column('place_id', sa.String(length=255), nullable=True))

    fee_cols = _columns('delivery_fee_configs')
    with op.batch_alter_table('delivery_fee_configs', schema=None) as batch_op:
        if 'depot' not in fee_cols:
            batch_op.add_column(sa.Column('depot', mysql.JSON(), nullable=True))
        if 'distance_surcharges' not in fee_cols:
            batch_op.add_column(sa.Column('distance_surcharges', mysql.JSON(), nullable=True))
        if 'beyond_surcharge' not in fee_cols:
            batch_op.add_column(sa.Column(
                'beyond_surcharge',
                mysql.NUMERIC(precision=10, scale=2),
                nullable=False,
                server_default='0',
            ))
        if 'beyond_label' not in fee_cols:
            batch_op.add_column(sa.Column('beyond_label', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('delivery_fee_configs', schema=None) as batch_op:
        batch_op.drop_column('beyond_label')
        batch_op.drop_column('beyond_surcharge')
        batch_op.drop_column('distance_surcharges')
        batch_op.drop_column('depot')

    with op.batch_alter_table('addresses', schema=None) as batch_op:
        batch_op.drop_column('place_id')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
