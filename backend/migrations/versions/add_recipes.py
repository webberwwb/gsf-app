"""Add recipe community tables.

Revision ID: add_recipes
Revises: add_product_deleted_at
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_recipes'
down_revision = 'add_product_deleted_at'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'recipes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('author_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('title', sa.String(80), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('images', sa.JSON(), nullable=False),
        sa.Column('cover_image', sa.String(512), nullable=False),
        sa.Column('heart_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('collect_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comment_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('rewarded_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_recipes_author_user_id', 'recipes', ['author_user_id'])
    op.create_index('ix_recipes_deleted_at', 'recipes', ['deleted_at'])

    op.create_table(
        'recipe_products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('recipe_id', 'product_id', name='uq_recipe_product'),
    )
    op.create_index('ix_recipe_products_recipe_id', 'recipe_products', ['recipe_id'])
    op.create_index('ix_recipe_products_product_id', 'recipe_products', ['product_id'])

    op.create_table(
        'recipe_hearts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('recipe_id', 'user_id', name='uq_recipe_heart'),
    )
    op.create_index('ix_recipe_hearts_recipe_id', 'recipe_hearts', ['recipe_id'])
    op.create_index('ix_recipe_hearts_user_id', 'recipe_hearts', ['user_id'])

    op.create_table(
        'recipe_collects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('recipe_id', 'user_id', name='uq_recipe_collect'),
    )
    op.create_index('ix_recipe_collects_recipe_id', 'recipe_collects', ['recipe_id'])
    op.create_index('ix_recipe_collects_user_id', 'recipe_collects', ['user_id'])

    op.create_table(
        'recipe_comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('recipe_id', sa.Integer(), sa.ForeignKey('recipes.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('recipe_comments.id'), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_recipe_comments_recipe_id', 'recipe_comments', ['recipe_id'])
    op.create_index('ix_recipe_comments_user_id', 'recipe_comments', ['user_id'])
    op.create_index('ix_recipe_comments_parent_id', 'recipe_comments', ['parent_id'])
    op.create_index('ix_recipe_comments_deleted_at', 'recipe_comments', ['deleted_at'])


def downgrade():
    op.drop_table('recipe_comments')
    op.drop_table('recipe_collects')
    op.drop_table('recipe_hearts')
    op.drop_table('recipe_products')
    op.drop_table('recipes')
