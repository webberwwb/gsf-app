"""add_commission_excluded_users

Revision ID: add_commission_excluded_users
Revises: product_sort_order_decimal
Create Date: 2026-06-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision = 'add_commission_excluded_users'
down_revision = 'product_sort_order_decimal'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'commission_excluded_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    with op.batch_alter_table('commission_excluded_users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_commission_excluded_users_user_id'), ['user_id'], unique=True)

    # Migrate the previously hardcoded exclusion (谷语农庄)
    conn = op.get_bind()
    result = conn.execute(text("SELECT id FROM users WHERE phone = '+14373406925' LIMIT 1"))
    row = result.fetchone()
    if row:
        conn.execute(
            text(
                "INSERT INTO commission_excluded_users (user_id, notes, created_at, updated_at) "
                "VALUES (:user_id, :notes, NOW(), NOW())"
            ),
            {'user_id': row[0], 'notes': '谷语农庄'},
        )


def downgrade():
    with op.batch_alter_table('commission_excluded_users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_commission_excluded_users_user_id'))
    op.drop_table('commission_excluded_users')
