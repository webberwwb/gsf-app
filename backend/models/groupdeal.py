from models.base import BaseModel
from models import db
from datetime import datetime

class GroupDeal(BaseModel):
    """Group Deal model - creates group buy events with order window and pickup date"""
    __tablename__ = 'group_deals'
    
    # Deal info
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Order window: when users can place orders
    order_start_date = db.Column(db.DateTime, nullable=False)
    order_end_date = db.Column(db.DateTime, nullable=False)
    
    # Pickup date: when users can pick up their orders
    pickup_date = db.Column(db.DateTime, nullable=False)
    
    # Deal status
    status = db.Column(db.String(50), default='upcoming', nullable=False)  # 'upcoming', 'active', 'closed', 'completed'
    
    # Relationships
    products = db.relationship('GroupDealProduct', backref='group_deal', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='group_deal', lazy=True)
    
    @property
    def is_active(self):
        """Check if deal is currently active (within order window)"""
        now = datetime.utcnow()
        return (
            self.status == 'active' and
            self.order_start_date <= now <= self.order_end_date
        )
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'title': self.title,
            'description': self.description,
            'order_start_date': self.order_start_date.isoformat() if self.order_start_date else None,
            'order_end_date': self.order_end_date.isoformat() if self.order_end_date else None,
            'pickup_date': self.pickup_date.isoformat() if self.pickup_date else None,
            'status': self.status,
            'is_active': self.is_active
        })
        return data

class GroupDealProduct(BaseModel):
    """Junction table: Products available in a Group Deal"""
    __tablename__ = 'group_deal_products'
    
    group_deal_id = db.Column(db.Integer, db.ForeignKey('group_deals.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    # Override prices for this deal (optional)
    deal_price = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Stock limit for this deal (optional)
    deal_stock_limit = db.Column(db.Integer, nullable=True)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'group_deal_id': self.group_deal_id,
            'product_id': self.product_id,
            'deal_price': float(self.deal_price) if self.deal_price else None,
            'deal_stock_limit': self.deal_stock_limit
        })
        return data

