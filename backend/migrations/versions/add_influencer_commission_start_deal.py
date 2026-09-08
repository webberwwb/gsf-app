"""Add optional 推荐官 commission start group-deal cutoff.

Revision ID: add_inf_commission_start_deal
Revises: convert_phone_sdr_to_influencer
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_inf_commission_start_deal'
down_revision = 'convert_phone_sdr_to_influencer'
branch_labels = None
depends_on = None

OWNER_PHONE = '+15196142735'
START_GROUP_DEAL_ID = 27


def upgrade():
    op.add_column(
        'influencer_profiles',
        sa.Column('commission_from_group_deal_id', sa.Integer(), nullable=True),
    )
    conn = op.get_bind()
    owner = conn.execute(
        sa.text('SELECT id FROM users WHERE phone = :phone LIMIT 1'),
        {'phone': OWNER_PHONE},
    ).fetchone()
    if owner:
        conn.execute(
            sa.text(
                'UPDATE influencer_profiles '
                'SET commission_from_group_deal_id = :deal_id '
                'WHERE user_id = :user_id'
            ),
            {'deal_id': START_GROUP_DEAL_ID, 'user_id': owner[0]},
        )


def downgrade():
    op.drop_column('influencer_profiles', 'commission_from_group_deal_id')
