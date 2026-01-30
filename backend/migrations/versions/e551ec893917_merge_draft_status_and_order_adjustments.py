"""merge draft status and order adjustments

Revision ID: e551ec893917
Revises: add_draft_status, add_order_adjustments
Create Date: 2026-01-30 08:17:21.714198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e551ec893917'
down_revision = ('add_draft_status', 'add_order_adjustments')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
