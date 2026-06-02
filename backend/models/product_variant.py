from models.base import BaseModel
from models import db
from sqlalchemy import Numeric


class ProductVariant(BaseModel):
    """Product variant (spec) option with price delta"""
    __tablename__ = 'product_variants'

    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    price_delta = db.Column(Numeric(10, 2), default=0, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    product = db.relationship('Product', back_populates='variants')

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'product_id': self.product_id,
            'name': self.name,
            'price_delta': float(self.price_delta) if self.price_delta is not None else 0.0,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        })
        return data
