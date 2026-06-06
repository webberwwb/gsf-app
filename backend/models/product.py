from models.base import BaseModel
from models import db
from sqlalchemy import JSON, Numeric

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
    # - unit_weight: {"price_per_unit": 5.00, "unit": "lb"}
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
    
    # Category relationship (optional)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=True, index=True)
    
    # Whether this product counts toward the free shipping threshold ($150)
    # If False, product price won't be included in subtotal calculation for free shipping
    counts_toward_free_shipping = db.Column(db.Boolean, default=True, nullable=False)
    
    # Custom sort order (lower numbers appear first; decimals allowed e.g. 1.1 between 1 and 2)
    sort_order = db.Column(db.Numeric(12, 4), default=0, nullable=False, index=True)

    # Embedded substitute product (when primary is unavailable)
    substitute_enabled = db.Column(db.Boolean, default=False, nullable=False)
    substitute_name = db.Column(db.String(255), nullable=True)
    substitute_description = db.Column(db.Text, nullable=True)
    substitute_images = db.Column(JSON, nullable=True)
    substitute_price = db.Column(Numeric(10, 2), nullable=True)  # legacy; use substitute_pricing_*
    substitute_pricing_type = db.Column(db.String(20), nullable=True)
    substitute_pricing_data = db.Column(JSON, nullable=True)
    
    # Relationships
    group_deal_products = db.relationship('GroupDealProduct', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    variants = db.relationship(
        'ProductVariant',
        back_populates='product',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='ProductVariant.sort_order',
    )
    
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
        from utils.order_item_pricing import get_display_price_from_config
        return get_display_price_from_config(self.pricing_type, self.pricing_data)
    
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
            # unit_weight: products are weighed individually, not stacked
            # unit_price = price_per_unit (the rate)
            # total_price = price_per_unit * weight (or estimated weight)
            # Quantity is always 1 for weight-based products (they're weighed individually, not stacked)
            if not weight or not self.pricing_data or 'price_per_unit' not in self.pricing_data:
                return None
            price_per_unit = float(self.pricing_data['price_per_unit'])
            return price_per_unit * weight  # No quantity multiplication
        elif self.pricing_type == 'bundled_weight':
            # bundled_weight: products are weighed individually, not stacked
            # unit_price = price_per_unit (the rate)
            # total_price = price_per_unit * weight (or estimated weight)
            # Quantity is always 1 for weight-based products (they're weighed individually, not stacked)
            if not self.pricing_data or 'price_per_unit' not in self.pricing_data:
                return None
            price_per_unit = float(self.pricing_data['price_per_unit'])
            # If weight is provided, use it; otherwise return None (needs weight)
            if weight:
                return price_per_unit * weight  # No quantity multiplication
            return None
        return None
    
    def get_active_variants(self):
        return [v for v in (self.variants or []) if v.is_active]

    def get_substitute_pricing_type(self):
        """Effective substitute pricing type (falls back to product pricing_type)."""
        if self.substitute_pricing_type:
            return self.substitute_pricing_type
        if self.substitute_price is not None:
            return 'per_item'
        return self.pricing_type

    def get_substitute_pricing_data(self):
        """Effective substitute pricing_data JSON."""
        if self.substitute_pricing_data:
            return self.substitute_pricing_data
        if self.substitute_price is not None:
            return {'price': float(self.substitute_price)}
        return self.pricing_data

    def get_substitute_display_price(self):
        """Display price for substitute using its pricing model."""
        from utils.order_item_pricing import get_display_price_from_config
        return get_display_price_from_config(
            self.get_substitute_pricing_type(),
            self.get_substitute_pricing_data(),
        )

    def get_substitute_dict(self):
        if not self.substitute_enabled:
            return None
        images = self.substitute_images if self.substitute_images and isinstance(self.substitute_images, list) else []
        pt = self.get_substitute_pricing_type()
        pd = self.get_substitute_pricing_data()
        return {
            'enabled': True,
            'name': self.substitute_name,
            'description': self.substitute_description,
            'images': images,
            'image': images[0] if images else None,
            'pricing_type': pt,
            'pricing_data': pd,
            'price': self.get_substitute_display_price(),
        }

    def to_dict(self, include_all_variants=False):
        data = super().to_dict()
        # Convert images: use images array if available, otherwise convert single image to array
        images = self.images if self.images and isinstance(self.images, list) else []
        if not images and self.image:
            images = [self.image]
        
        variant_list = self.variants if include_all_variants else self.get_active_variants()
        variants_data = [v.to_dict() for v in sorted(variant_list, key=lambda x: x.sort_order)]

        data.update({
            'name': self.name,
            'image': images[0] if images else None,  # Keep for backward compatibility
            'images': images,  # New multiple images array
            'pricing_type': self.pricing_type,
            'pricing_data': self.pricing_data,
            'price': self.get_display_price(),  # Main price field for FE (2-decimal rounded)
            'display_price': self.get_display_price(),
            'description': self.description,
            'stock_limit': self.stock_limit,
            'is_active': self.is_active,
            'is_available': self.is_available,
            'supplier_id': self.supplier_id,
            'supplier': self.supplier.to_dict() if self.supplier else None,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'counts_toward_free_shipping': self.counts_toward_free_shipping,
            'sort_order': float(self.sort_order) if self.sort_order is not None else 0,
            'variants': variants_data,
            'substitute_enabled': self.substitute_enabled,
            'substitute': self.get_substitute_dict(),
        })
        return data

