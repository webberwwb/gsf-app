"""merge user_source and other heads

Revision ID: 185ab432aa9d
Revises: add_prod_free_shipping_flag, remove_deal_price_column, add_user_source
Create Date: 2026-01-19 16:32:10.009425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '185ab432aa9d'
down_revision = ('add_prod_free_shipping_flag', 'remove_deal_price_column', 'add_user_source')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
