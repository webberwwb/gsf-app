"""Migrate customer_feedback.outcome from English slugs to Chinese labels

Revision ID: migrate_feedback_outcome_cn
Revises: add_customer_feedback
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa


revision = 'migrate_feedback_outcome_cn'
down_revision = 'add_customer_feedback'
branch_labels = None
depends_on = None


# Old slug -> new stored label (matches FeedbackOutcome)
_UPGRADE_MAP = (
    ('will_not_follow', '不跟进'),
    ('no_answer', '未回复'),
    ('pending', '未联系'),
    ('reached', '再次跟进'),
)

_DOWNGRADE_MAP = (
    ('不跟进', 'will_not_follow'),
    ('未回复', 'no_answer'),
    ('未联系', 'pending'),
    ('再次跟进', 'reached'),
)


def upgrade():
    conn = op.get_bind()
    for old, new in _UPGRADE_MAP:
        conn.execute(
            sa.text(
                'UPDATE customer_feedback SET outcome = :new WHERE outcome = :old'
            ),
            {'new': new, 'old': old},
        )
    op.alter_column(
        'customer_feedback',
        'outcome',
        existing_type=sa.String(length=32),
        server_default='未联系',
        existing_nullable=False,
    )


def downgrade():
    conn = op.get_bind()
    for new, old in _DOWNGRADE_MAP:
        conn.execute(
            sa.text(
                'UPDATE customer_feedback SET outcome = :old WHERE outcome = :new'
            ),
            {'new': new, 'old': old},
        )
    op.alter_column(
        'customer_feedback',
        'outcome',
        existing_type=sa.String(length=32),
        server_default='reached',
        existing_nullable=False,
    )
