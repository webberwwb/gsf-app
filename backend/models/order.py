from models.base import BaseModel
from models import db
from sqlalchemy import Numeric
from datetime import datetime

class Order(BaseModel):
    """Order model - tracks order details, payment, pickup status, and points"""
    __tablename__ = 'orders'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    group_deal_id = db.Column(db.Integer, db.ForeignKey('group_deals.id'), nullable=False, index=True)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True)  # Optional delivery address
    
    # Order number (unique identifier)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Order totals
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    tax = db.Column(Numeric(10, 2), default=0, nullable=False)
    total = db.Column(Numeric(10, 2), nullable=False)
    
    # Points accumulated for this order (1 point per dollar)
    points_earned = db.Column(db.Integer, default=0, nullable=False)
    
    # Payment status
    payment_status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'paid', 'failed', 'refunded'
    payment_method = db.Column(db.String(50), nullable=True)  # 'cash', 'card', 'online', etc.
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_transaction_id = db.Column(db.String(255), nullable=True)
    
    # Pickup status
    pickup_status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'ready', 'picked_up', 'cancelled'
    pickup_date = db.Column(db.DateTime, nullable=True)
    
    # Order status
    status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'confirmed', 'processing', 'completed', 'cancelled'
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    address = db.relationship('Address', backref='orders')
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'group_deal_id': self.group_deal_id,
            'address_id': self.address_id,
            'order_number': self.order_number,
            'subtotal': float(self.subtotal) if self.subtotal else None,
            'tax': float(self.tax) if self.tax else None,
            'total': float(self.total) if self.total else None,
            'points_earned': self.points_earned,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_transaction_id': self.payment_transaction_id,
            'pickup_status': self.pickup_status,
            'pickup_date': self.pickup_date.isoformat() if self.pickup_date else None,
            'status': self.status,
            'notes': self.notes
        })
        return data

class OrderItem(BaseModel):
    """Order Item model - individual items in an order"""
    __tablename__ = 'order_items'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(Numeric(10, 2), nullable=False)
    total_price = db.Column(Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'total_price': float(self.total_price) if self.total_price else None
        })
        return data

