from models.base import BaseModel
from models import db
from sqlalchemy import JSON

class Product(BaseModel):
    """Product model"""
    __tablename__ = 'products'
    
    name = db.Column(db.String(255), nullable=False, index=True)
    image = db.Column(db.String(512), nullable=True)  # URL to product image (deprecated, use images)
    images = db.Column(JSON, nullable=True)  # Array of image URLs
    
    # Pricing type: determines how the product is priced
    pricing_type = db.Column(db.String(20), default='per_item', nullable=False)
    
    # Pricing data (JSON) - main pricing field
    # Structure depends on pricing_type:
    # - per_item: {"price": 10.00}
    # - weight_range: {"ranges": [{"min": 0, "max": 2, "price": 10.00}, ...]}
    # - unit_weight: {"price_per_unit": 5.00, "unit": "kg"}
    # - bundled_weight: {"price_per_unit": 5.00, "unit": "lb", "min_weight": 7, "max_weight": 15}
    pricing_data = db.Column(JSON, nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    
    # Stock limit: None/null means unlimited, otherwise number available
    stock_limit = db.Column(db.Integer, nullable=True)
    
    # Product status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Supplier relationship (optional)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True, index=True)
    supplier = db.relationship('Supplier', backref='products', lazy=True)
    
    # Whether this product counts toward the free shipping threshold ($150)
    # If False, product price won't be included in subtotal calculation for free shipping
    counts_toward_free_shipping = db.Column(db.Boolean, default=True, nullable=False)
    
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
        """Get display price - the default price shown to customers"""
        if self.pricing_type == 'per_item':
            if self.pricing_data and 'price' in self.pricing_data:
                return float(self.pricing_data['price'])
            return None
        elif self.pricing_type == 'weight_range':
            if self.pricing_data and 'ranges' in self.pricing_data:
                ranges = self.pricing_data['ranges']
                if ranges:
                    return float(ranges[0].get('price', 0))
            return None
        elif self.pricing_type == 'unit_weight':
            if self.pricing_data and 'price_per_unit' in self.pricing_data:
                return float(self.pricing_data['price_per_unit'])
            return None
        elif self.pricing_type == 'bundled_weight':
            if self.pricing_data and 'price_per_unit' in self.pricing_data:
                # Return average price for display (using mid-point weight)
                price_per_unit = float(self.pricing_data['price_per_unit'])
                min_weight = float(self.pricing_data.get('min_weight', 7))
                max_weight = float(self.pricing_data.get('max_weight', 15))
                avg_weight = (min_weight + max_weight) / 2
                return price_per_unit * avg_weight
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
        elif self.pricing_type == 'bundled_weight':
            # quantity = number of packages
            # Each package has variable weight between min_weight and max_weight
            if not self.pricing_data or 'price_per_unit' not in self.pricing_data:
                return None
            price_per_unit = float(self.pricing_data['price_per_unit'])
            # If weight is provided, use it; otherwise return None (needs weight)
            if weight:
                return price_per_unit * weight * quantity
            return None
        return None
    
    def to_dict(self):
        data = super().to_dict()
        # Convert images: use images array if available, otherwise convert single image to array
        images = self.images if self.images and isinstance(self.images, list) else []
        if not images and self.image:
            images = [self.image]
        
        data.update({
            'name': self.name,
            'image': images[0] if images else None,  # Keep for backward compatibility
            'images': images,  # New multiple images array
            'pricing_type': self.pricing_type,
            'pricing_data': self.pricing_data,
            'price': self.get_display_price(),  # Main price field for FE
            'description': self.description,
            'stock_limit': self.stock_limit,
            'is_active': self.is_active,
            'is_available': self.is_available,
            'supplier_id': self.supplier_id,
            'supplier': self.supplier.to_dict() if self.supplier else None,
            'counts_toward_free_shipping': self.counts_toward_free_shipping
        })
        return data

