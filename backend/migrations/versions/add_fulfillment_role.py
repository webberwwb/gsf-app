"""Add fulfillment role tables, order delivery assignment fields, and seed 配货员.

Revision ID: add_fulfillment_role
Revises: add_inf_commission_start_deal
Create Date: 2026-09-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = 'add_fulfillment_role'
down_revision = 'add_inf_commission_start_deal'
branch_labels = None
depends_on = None


SEED_FULFILLMENT_EMAILS = (
    'webberwwb@gmail.com',
    'forlove.dxy@gmail.com',
)


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    order_cols = {col['name'] for col in inspector.get_columns('orders')}

    if 'delivery_handler' not in order_cols:
        op.add_column(
            'orders',
            sa.Column('delivery_handler', sa.String(20), nullable=False, server_default='unassigned'),
        )
    if 'delivery_assignee_id' not in order_cols:
        op.add_column('orders', sa.Column('delivery_assignee_id', sa.Integer(), nullable=True))
        op.create_index('ix_orders_delivery_assignee_id', 'orders', ['delivery_assignee_id'])
        op.create_foreign_key(
            'fk_orders_delivery_assignee_id_users',
            'orders',
            'users',
            ['delivery_assignee_id'],
            ['id'],
        )
    if 'delivery_route_seq' not in order_cols:
        op.add_column('orders', sa.Column('delivery_route_seq', sa.Integer(), nullable=True))
    if 'delivery_photo_url' not in order_cols:
        op.add_column('orders', sa.Column('delivery_photo_url', sa.String(512), nullable=True))
    if 'delivered_at' not in order_cols:
        op.add_column('orders', sa.Column('delivered_at', sa.DateTime(), nullable=True))
    if 'third_party_note' not in order_cols:
        op.add_column('orders', sa.Column('third_party_note', sa.String(255), nullable=True))
    if 'delivery_fee_earned' not in order_cols:
        op.add_column('orders', sa.Column('delivery_fee_earned', sa.Numeric(10, 2), nullable=True))

    tables = set(inspector.get_table_names())
    if 'fulfillment_profiles' not in tables:
        op.create_table(
            'fulfillment_profiles',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
            sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False, server_default='0'),
            sa.Column('delivery_fee_per_order', sa.Numeric(10, 2), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index('ix_fulfillment_profiles_user_id', 'fulfillment_profiles', ['user_id'])

    if 'fulfillment_work_sessions' not in tables:
        op.create_table(
            'fulfillment_work_sessions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('work_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=False),
            sa.Column('end_time', sa.Time(), nullable=True),
            sa.Column('hours', sa.Numeric(6, 2), nullable=True),
            sa.Column('notes', sa.String(255), nullable=True),
            sa.Column('group_deal_id', sa.Integer(), sa.ForeignKey('group_deals.id'), nullable=True),
            sa.Column('hourly_rate_snapshot', sa.Numeric(10, 2), nullable=True),
            sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        )
        op.create_index('ix_fulfillment_work_sessions_user_id', 'fulfillment_work_sessions', ['user_id'])
        op.create_index('ix_fulfillment_work_sessions_work_date', 'fulfillment_work_sessions', ['work_date'])

    if 'fulfillment_payouts' not in tables:
        op.create_table(
            'fulfillment_payouts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('paid_at', sa.DateTime(), nullable=False),
            sa.Column('notes', sa.String(255), nullable=True),
            sa.Column('paid_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        )
        op.create_index('ix_fulfillment_payouts_user_id', 'fulfillment_payouts', ['user_id'])

    now = sa.func.now()
    users = sa.table(
        'users',
        sa.column('id', sa.Integer),
        sa.column('email', sa.String),
        sa.column('nickname', sa.String),
        sa.column('phone', sa.String),
        sa.column('status', sa.String),
        sa.column('points', sa.Integer),
        sa.column('creation_date', sa.DateTime),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    roles = sa.table(
        'user_roles',
        sa.column('id', sa.Integer),
        sa.column('user_id', sa.Integer),
        sa.column('role', sa.String),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    profiles = sa.table(
        'fulfillment_profiles',
        sa.column('id', sa.Integer),
        sa.column('user_id', sa.Integer),
        sa.column('hourly_rate', sa.Numeric),
        sa.column('delivery_fee_per_order', sa.Numeric),
        sa.column('is_active', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    conn = op.get_bind()
    for email in SEED_FULFILLMENT_EMAILS:
        existing = conn.execute(
            sa.text('SELECT id FROM users WHERE LOWER(email) = LOWER(:email)'),
            {'email': email},
        ).fetchone()
        if existing:
            user_id = existing[0]
        else:
            nickname = email.split('@')[0]
            conn.execute(
                users.insert().values(
                    email=email,
                    nickname=nickname,
                    phone=None,
                    status='active',
                    points=0,
                    creation_date=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            user_id = conn.execute(
                sa.text('SELECT id FROM users WHERE LOWER(email) = LOWER(:email)'),
                {'email': email},
            ).scalar()

        has_role = conn.execute(
            sa.text(
                'SELECT id FROM user_roles WHERE user_id = :user_id AND role = :role'
            ),
            {'user_id': user_id, 'role': 'fulfillment'},
        ).fetchone()
        if not has_role:
            conn.execute(
                roles.insert().values(
                    user_id=user_id,
                    role='fulfillment',
                    created_at=now,
                    updated_at=now,
                )
            )

        has_profile = conn.execute(
            sa.text('SELECT id FROM fulfillment_profiles WHERE user_id = :user_id'),
            {'user_id': user_id},
        ).fetchone()
        if not has_profile:
            conn.execute(
                profiles.insert().values(
                    user_id=user_id,
                    hourly_rate=0,
                    delivery_fee_per_order=0,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )


def downgrade():
    op.drop_table('fulfillment_payouts')
    op.drop_table('fulfillment_work_sessions')
    op.drop_table('fulfillment_profiles')
    op.drop_constraint('fk_orders_delivery_assignee_id_users', 'orders', type_='foreignkey')
    op.drop_index('ix_orders_delivery_assignee_id', table_name='orders')
    op.drop_column('orders', 'delivery_fee_earned')
    op.drop_column('orders', 'third_party_note')
    op.drop_column('orders', 'delivered_at')
    op.drop_column('orders', 'delivery_photo_url')
    op.drop_column('orders', 'delivery_route_seq')
    op.drop_column('orders', 'delivery_assignee_id')
    op.drop_column('orders', 'delivery_handler')
