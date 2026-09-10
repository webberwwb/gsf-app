"""add_delivery_consent

Revision ID: add_delivery_consent
Revises: add_fulfillment_role
Create Date: 2026-09-09

Store one-time delivery 须知 acceptance on the user.
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_delivery_consent'
down_revision = 'add_fulfillment_role'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delivery_consent_accepted_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('delivery_consent_version', sa.String(length=16), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('delivery_consent_version')
        batch_op.drop_column('delivery_consent_accepted_at')
