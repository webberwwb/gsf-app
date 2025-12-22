from models.base import BaseModel
from models import db
from sqlalchemy import Numeric, JSON, Enum as SQLEnum
import json

class Product(BaseModel):
    """Product model"""
    __tablename__ = 'products'
    
    name = db.Column(db.String(255), nullable=False, index=True)
    image = db.Column(db.String(512), nullable=True)  # URL to product image
    
    # Pricing type: 'per_item', 'weight_range', 'unit_weight'
    pricing_type = db.Column(db.String(20), default='per_item', nullable=False)
    
    # Legacy pricing fields (for backward compatibility)
    original_price = db.Column(Numeric(10, 2), nullable=True)
    sale_price = db.Column(Numeric(10, 2), nullable=True)
    
    # Pricing data (JSON) - structure depends on pricing_type
    # For 'per_item': {"original_price": 10.00, "sale_price": 8.00}
    # For 'weight_range': {"ranges": [{"min": 0, "max": 2, "price": 10.00}, {"min": 2, "max": 4, "price": 15.00}, {"min": 4, "max": null, "price": 20.00}]}
    # For 'unit_weight': {"price_per_unit": 5.00, "unit": "kg"} or {"price_per_unit": 2.5, "unit": "lb"}
    pricing_data = db.Column(JSON, nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    
    # Stock limit: None/null means unlimited, otherwise number available
    stock_limit = db.Column(db.Integer, nullable=True)
    
    # Product status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Supplier relationship (optional)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True, index=True)
    supplier = db.relationship('Supplier', backref='products', lazy=True)
    
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
    
    def get_display_price(self):
        """Get display price based on pricing type"""
        if self.pricing_type == 'per_item':
            if self.pricing_data and 'sale_price' in self.pricing_data:
                return float(self.pricing_data['sale_price'])
            return float(self.sale_price) if self.sale_price else None
        elif self.pricing_type == 'weight_range':
            if self.pricing_data and 'ranges' in self.pricing_data:
                ranges = self.pricing_data['ranges']
                if ranges:
                    # Return first range price as display price
                    return float(ranges[0].get('price', 0))
            return None
        elif self.pricing_type == 'unit_weight':
            if self.pricing_data and 'price_per_unit' in self.pricing_data:
                return float(self.pricing_data['price_per_unit'])
            return None
        return None
    
    def calculate_price(self, quantity=1, weight=None):
        """Calculate price based on pricing type, quantity, and weight"""
        if self.pricing_type == 'per_item':
            price = self.get_display_price()
            return price * quantity if price else None
        elif self.pricing_type == 'weight_range':
            if not weight or not self.pricing_data or 'ranges' not in self.pricing_data:
                return None
            ranges = self.pricing_data['ranges']
            for range_item in ranges:
                min_weight = range_item.get('min', 0)
                max_weight = range_item.get('max')
                if weight >= min_weight and (max_weight is None or weight < max_weight):
                    return float(range_item.get('price', 0)) * quantity
            return None
        elif self.pricing_type == 'unit_weight':
            if not weight or not self.pricing_data or 'price_per_unit' not in self.pricing_data:
                return None
            price_per_unit = float(self.pricing_data['price_per_unit'])
            return price_per_unit * weight * quantity
        return None
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'image': self.image,
            'pricing_type': self.pricing_type,
            'pricing_data': self.pricing_data,
            'original_price': float(self.original_price) if self.original_price else None,
            'sale_price': float(self.sale_price) if self.sale_price else None,
            'display_price': self.get_display_price(),
            'description': self.description,
            'stock_limit': self.stock_limit,
            'is_active': self.is_active,
            'is_available': self.is_available,
            'supplier_id': self.supplier_id,
            'supplier': self.supplier.to_dict() if self.supplier else None
        })
        return data

