"""Public recipe posts, linked products, hearts, collects, and comments."""
from models import db
from models.base import BaseModel, est_now
from sqlalchemy import JSON, UniqueConstraint


class Recipe(BaseModel):
    __tablename__ = 'recipes'

    author_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    source = db.Column(db.String(20), nullable=False, default='user')  # user | official
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sides = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    cook_time = db.Column(db.String(20), nullable=True)
    images = db.Column(JSON, nullable=False)
    cover_image = db.Column(db.String(512), nullable=False)
    heart_count = db.Column(db.Integer, nullable=False, default=0)
    collect_count = db.Column(db.Integer, nullable=False, default=0)
    comment_count = db.Column(db.Integer, nullable=False, default=0)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    rewarded_at = db.Column(db.DateTime, nullable=True)

    author = db.relationship('User', foreign_keys=[author_user_id])
    product_links = db.relationship(
        'RecipeProduct',
        back_populates='recipe',
        cascade='all, delete-orphan',
        order_by='RecipeProduct.sort_order',
    )

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class RecipeProduct(db.Model):
    __tablename__ = 'recipe_products'
    __table_args__ = (
        UniqueConstraint('recipe_id', 'product_id', name='uq_recipe_product'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    recipe = db.relationship('Recipe', back_populates='product_links')
    product = db.relationship('Product')


class RecipeHeart(db.Model):
    __tablename__ = 'recipe_hearts'
    __table_args__ = (
        UniqueConstraint('recipe_id', 'user_id', name='uq_recipe_heart'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=est_now, nullable=False)


class RecipeCollect(db.Model):
    __tablename__ = 'recipe_collects'
    __table_args__ = (
        UniqueConstraint('recipe_id', 'user_id', name='uq_recipe_collect'),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=est_now, nullable=False)


class RecipeComment(BaseModel):
    __tablename__ = 'recipe_comments'

    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('recipe_comments.id'), nullable=True, index=True)
    body = db.Column(db.Text, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    author = db.relationship('User', foreign_keys=[user_id])
    recipe = db.relationship('Recipe', foreign_keys=[recipe_id])
