from models.base import BaseModel
from models import db
from sqlalchemy import Numeric

class Product(BaseModel):
    """Product model"""
    __tablename__ = 'products'
    
    name = db.Column(db.String(255), nullable=False, index=True)
    image = db.Column(db.String(512), nullable=True)  # URL to product image
    original_price = db.Column(Numeric(10, 2), nullable=False)
    sale_price = db.Column(Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Stock limit: None/null means unlimited, otherwise number available
    stock_limit = db.Column(db.Integer, nullable=True)
    
    # Product status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    group_deal_products = db.relationship('GroupDealProduct', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    @property
    def is_available(self):
        """Check if product is available (active and in stock)"""
        if not self.is_active:
            return False
        if self.stock_limit is None:
            return True
        # TODO: Calculate available stock from orders
        return True
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'image': self.image,
            'original_price': float(self.original_price) if self.original_price else None,
            'sale_price': float(self.sale_price) if self.sale_price else None,
            'description': self.description,
            'stock_limit': self.stock_limit,
            'is_active': self.is_active,
            'is_available': self.is_available
        })
        return data

