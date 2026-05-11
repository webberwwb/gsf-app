"""Store credit, referrals, referral program config

Revision ID: add_store_credit_referrals
Revises: add_product_categories
Create Date: 2026-05-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import secrets

revision = 'add_store_credit_referrals'
down_revision = 'add_product_categories'
branch_labels = None
depends_on = None

_REF_ALPH = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'


def upgrade():
    op.add_column(
        'users',
        sa.Column('store_credit_balance', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False)
    )
    op.add_column('users', sa.Column('referral_code', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('referred_by_user_id', sa.Integer(), nullable=True))
    op.create_index('ix_users_referral_code', 'users', ['referral_code'], unique=True)
    op.create_index('ix_users_referred_by_user_id', 'users', ['referred_by_user_id'], unique=False)
    op.create_foreign_key(
        'fk_users_referred_by_user_id',
        'users', 'users',
        ['referred_by_user_id'], ['id'],
    )

    op.add_column(
        'orders',
        sa.Column('store_credit_applied', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False)
    )

    op.create_table(
        'credit_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('balance_after', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tx_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_by_admin_user_id', sa.Integer(), nullable=True),
        sa.Column('related_order_id', sa.Integer(), nullable=True),
        sa.Column('related_referral_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_admin_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['related_order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_credit_transactions_user_id', 'credit_transactions', ['user_id'], unique=False)
    op.create_index('ix_credit_transactions_tx_type', 'credit_transactions', ['tx_type'], unique=False)
    op.create_index('ix_credit_transactions_related_order_id', 'credit_transactions', ['related_order_id'], unique=False)
    op.create_index('ix_credit_transactions_related_referral_id', 'credit_transactions', ['related_referral_id'], unique=False)

    op.create_table(
        'referral_program_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('invitee_bonus_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('inviter_reward_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'referral_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('inviter_user_id', sa.Integer(), nullable=False),
        sa.Column('invitee_user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('invitee_bonus_transaction_id', sa.Integer(), nullable=True),
        sa.Column('inviter_reward_transaction_id', sa.Integer(), nullable=True),
        sa.Column('first_completed_order_id', sa.Integer(), nullable=True),
        sa.Column('rewarded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['first_completed_order_id'], ['orders.id'], ),
        sa.ForeignKeyConstraint(['invitee_bonus_transaction_id'], ['credit_transactions.id'], ),
        sa.ForeignKeyConstraint(['invitee_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['inviter_reward_transaction_id'], ['credit_transactions.id'], ),
        sa.ForeignKeyConstraint(['inviter_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_referral_records_inviter_user_id', 'referral_records', ['inviter_user_id'], unique=False)
    op.create_index('ix_referral_records_invitee_user_id', 'referral_records', ['invitee_user_id'], unique=True)
    op.create_index('ix_referral_records_status', 'referral_records', ['status'], unique=False)

    op.execute("""
        INSERT INTO referral_program_configs
        (created_at, updated_at, invitee_bonus_amount, inviter_reward_amount, is_active)
        VALUES (NOW(), NOW(), 5.00, 5.00, 1)
    """)

    conn = op.get_bind()
    res = conn.execute(text(
        "SELECT DISTINCT user_id FROM orders WHERE status = 'completed' AND deleted_at IS NULL"
    ))
    user_ids = [row[0] for row in res.fetchall()]

    for uid in user_ids:
        for _ in range(80):
            code = ''.join(secrets.choice(_REF_ALPH) for _ in range(8))
            taken = conn.execute(
                text('SELECT id FROM users WHERE referral_code = :c LIMIT 1'),
                {'c': code},
            ).first()
            if not taken:
                conn.execute(
                    text('UPDATE users SET referral_code = :c WHERE id = :uid'),
                    {'c': code, 'uid': uid},
                )
                break


def downgrade():
    op.drop_index('ix_referral_records_status', table_name='referral_records')
    op.drop_index('ix_referral_records_invitee_user_id', table_name='referral_records')
    op.drop_index('ix_referral_records_inviter_user_id', table_name='referral_records')
    op.drop_table('referral_records')
    op.drop_table('referral_program_configs')
    op.drop_index('ix_credit_transactions_related_referral_id', table_name='credit_transactions')
    op.drop_index('ix_credit_transactions_related_order_id', table_name='credit_transactions')
    op.drop_index('ix_credit_transactions_tx_type', table_name='credit_transactions')
    op.drop_index('ix_credit_transactions_user_id', table_name='credit_transactions')
    op.drop_table('credit_transactions')
    op.drop_column('orders', 'store_credit_applied')
    op.drop_constraint('fk_users_referred_by_user_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_referred_by_user_id', table_name='users')
    op.drop_index('ix_users_referral_code', table_name='users')
    op.drop_column('users', 'referred_by_user_id')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'store_credit_balance')
