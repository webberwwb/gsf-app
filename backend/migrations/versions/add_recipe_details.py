"""Add recipe sides, difficulty, and cook time.

Revision ID: add_recipe_details
Revises: add_recipes
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_recipe_details'
down_revision = 'add_recipes'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recipes', sa.Column('sides', sa.Text(), nullable=True))
    op.add_column('recipes', sa.Column('difficulty', sa.String(20), nullable=True))
    op.add_column('recipes', sa.Column('cook_time', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('recipes', 'cook_time')
    op.drop_column('recipes', 'difficulty')
    op.drop_column('recipes', 'sides')
