"""Add suppliers table

Revision ID: add_suppliers_table
Revises: cf1c5204ff38
Create Date: 2024-12-21 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_suppliers_table'
down_revision = 'cf1c5204ff38'  # Latest migration: Add OTP tracking table
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('suppliers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('contact_person', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_name'), 'suppliers', ['name'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_suppliers_name'), table_name='suppliers')
    op.drop_table('suppliers')

