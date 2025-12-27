"""merge_migration_heads

Revision ID: 8a6d323dde12
Revises: unique_order_constraint, remove_legacy_price_fields
Create Date: 2025-12-26 10:45:06.224288

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a6d323dde12'
down_revision = ('unique_order_constraint', 'remove_legacy_price_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
