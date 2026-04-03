"""add quarterly bonus

Revision ID: 20260402164045
Revises: e59961bd59aa
Create Date: 2026-04-02 16:40:45.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260402164045'
down_revision = 'e59961bd59aa'
branch_labels = None
depends_on = None


def upgrade():
    # Create quarterly_bonuses table
    op.create_table('quarterly_bonuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sdr_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=False),
        sa.Column('commission_records_data', sa.JSON(), nullable=True),
        sa.Column('total_commission', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('bonus_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('bonus_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('payment_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['sdr_id'], ['sdrs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sdr_id', 'year', 'quarter', name='uq_sdr_year_quarter')
    )
    op.create_index(op.f('ix_quarterly_bonuses_sdr_id'), 'quarterly_bonuses', ['sdr_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_quarterly_bonuses_sdr_id'), table_name='quarterly_bonuses')
    op.drop_table('quarterly_bonuses')
