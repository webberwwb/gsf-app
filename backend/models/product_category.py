from models.base import BaseModel
from models import db

class ProductCategory(BaseModel):
    """Product Category model"""
    __tablename__ = 'product_categories'
    
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Custom sort order (lower numbers appear first)
    sort_order = db.Column(db.Integer, default=0, nullable=False, index=True)
    
    # Category status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        })
        return data
