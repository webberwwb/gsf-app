"""add_work_documents_and_action_items

Revision ID: e59961bd59aa
Revises: migrate_feedback_outcome_cn
Create Date: 2026-04-02 15:43:45.625192

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e59961bd59aa'
down_revision = 'migrate_feedback_outcome_cn'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('work_documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.Column('updated_by_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('action_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('assigned_to_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_by_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['document_id'], ['work_documents.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_action_items_assigned_to_id'), 'action_items', ['assigned_to_id'], unique=False)
    op.create_index(op.f('ix_action_items_document_id'), 'action_items', ['document_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_action_items_document_id'), table_name='action_items')
    op.drop_index(op.f('ix_action_items_assigned_to_id'), table_name='action_items')
    op.drop_table('action_items')
    op.drop_table('work_documents')
