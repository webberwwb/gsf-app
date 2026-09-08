"""Convert the phone-login SDR owner to 推荐官 and stop future SDR commission.

Revision ID: convert_phone_sdr_to_influencer
Revises: seed_influencer_product_rates
Create Date: 2026-09-07
"""
from alembic import op
import sqlalchemy as sa


revision = 'convert_phone_sdr_to_influencer'
down_revision = 'seed_influencer_product_rates'
branch_labels = None
depends_on = None

OWNER_PHONE = '+15196142735'


def upgrade():
    from flask import current_app
    from models.user import User
    from services import influencer_service

    if not current_app:
        return
    owner = User.query.filter_by(phone=OWNER_PHONE).first()
    if not owner:
        return
    google_ids = [
        row.id
        for row in User.query.filter(
            User.phone.is_(None),
            User.email.isnot(None),
            User.user_source.isnot(None),
            User.user_source == owner.user_source,
        ).all()
    ]
    from models import db
    influencer_service.convert_source_customers_to_influencer(
        owner.id,
        owner.user_source,
        exclude_user_ids=google_ids,
    )
    db.session.commit()


def downgrade():
    pass
