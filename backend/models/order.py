from models.base import BaseModel, utc_now
from models import db
from sqlalchemy import Numeric, and_
from sqlalchemy.orm import backref, foreign
from datetime import datetime
from constants.status_enums import OrderStatus, PaymentStatus, DeliveryMethod

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
    shipping_fee = db.Column(Numeric(10, 2), default=0, nullable=False)
    total = db.Column(Numeric(10, 2), nullable=False)

    # Store credit applied to this order (pre-tax/shipping total + adjustment semantics — see to_dict amount_due)
    store_credit_applied = db.Column(Numeric(10, 2), default=0, nullable=False)

    # Admin adjustment (can be positive or negative)
    # Negative = discount/deduction, Positive = addition/bonus
    adjustment_amount = db.Column(Numeric(10, 2), default=0, nullable=False)
    adjustment_notes = db.Column(db.Text, nullable=True)  # Notes explaining the adjustment
    
    # Points accumulated for this order (1 point per dollar)
    points_earned = db.Column(db.Integer, default=0, nullable=False)
    
    # Delivery method (see constants.status_enums.DeliveryMethod for valid values)
    delivery_method = db.Column(db.String(50), default=DeliveryMethod.PICKUP.value, nullable=False)
    
    # Pickup location (for pickup orders only)
    pickup_location = db.Column(db.String(100), nullable=True)  # e.g., 'markham', 'northyork'
    
    # Payment status (see constants.status_enums.PaymentStatus for valid values)
    payment_status = db.Column(db.String(50), default=PaymentStatus.UNPAID.value, nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)  # 'cash', 'card', 'online', etc.
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_transaction_id = db.Column(db.String(255), nullable=True)
    
    # Pickup status (kept for backwards compatibility)
    pickup_status = db.Column(db.String(50), default='pending', nullable=False)  # 'pending', 'ready', 'picked_up', 'cancelled'
    pickup_date = db.Column(db.DateTime, nullable=True)
    
    # Order status (see constants.status_enums.OrderStatus for valid values and workflow)
    # Workflow: submitted → confirmed → preparing → ready_for_pickup/out_for_delivery → completed
    status = db.Column(db.String(50), default=OrderStatus.SUBMITTED.value, nullable=False)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    # Set when this order was merged into another (see merged_into_order_id on survivor)
    merged_into_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    merged_at = db.Column(db.DateTime, nullable=True)
    
    # Active line items only (soft-deleted rows kept for audit / recovery)
    items = db.relationship(
        'OrderItem',
        backref=backref('order', lazy=True),
        lazy=True,
        cascade='save-update, merge',
        primaryjoin='and_(Order.id == foreign(OrderItem.order_id), OrderItem.deleted_at.is_(None))',
        foreign_keys='OrderItem.order_id',
    )
    all_items = db.relationship(
        'OrderItem',
        lazy=True,
        viewonly=True,
        overlaps='items,order',
        primaryjoin='Order.id == foreign(OrderItem.order_id)',
        foreign_keys='OrderItem.order_id',
    )
    address = db.relationship('Address', backref='orders')
    merged_into_order = db.relationship(
        'Order',
        remote_side='Order.id',
        foreign_keys='Order.merged_into_order_id',
        backref='merged_source_orders',
    )
    
    def to_dict(self, include_editable=True):
        data = super().to_dict()

        from utils.order_totals import calculate_amount_due

        subtotal_f = float(self.subtotal) if self.subtotal is not None else 0.0
        adjustment = float(self.adjustment_amount) if self.adjustment_amount is not None else 0.0
        shipping = float(self.shipping_fee) if self.shipping_fee is not None else 0.0
        base_total = float(self.total) if self.total is not None else 0.0
        credit_applied = float(self.store_credit_applied) if self.store_credit_applied is not None else 0.0
        amount_due = float(calculate_amount_due(self))
        final_total = base_total

        data.update({
            'user_id': self.user_id,
            'group_deal_id': self.group_deal_id,
            'address_id': self.address_id,
            'order_number': self.order_number,
            'subtotal': subtotal_f,
            'tax': float(self.tax) if self.tax is not None else 0.0,
            'shipping_fee': shipping,
            'total': base_total,
            'adjustment_amount': float(adjustment),
            'adjustment_notes': self.adjustment_notes,
            'final_total': final_total,
            'store_credit_applied': credit_applied,
            'amount_due': amount_due,
            'points_earned': self.points_earned,
            'delivery_method': self.delivery_method,
            'pickup_location': self.pickup_location,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_transaction_id': self.payment_transaction_id,
            'pickup_status': self.pickup_status,
            'pickup_date': self.pickup_date.isoformat() if self.pickup_date else None,
            'status': self.status,
            'notes': self.notes,
            'merged_into_order_id': self.merged_into_order_id,
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
        })
        
        # Add is_editable flag based on status
        if include_editable:
            # User can only edit/cancel when status is 'submitted'
            data['is_editable'] = self.status == 'submitted'
            # Check if order is past group deal end date for auto-confirm
            if hasattr(self, 'group_deal') and self.group_deal:
                from datetime import datetime
                now = datetime.utcnow()
                if self.status == 'submitted' and self.group_deal.order_end_date and now > self.group_deal.order_end_date:
                    data['should_be_confirmed'] = True
        
        return data

class OrderItem(BaseModel):
    """Order Item model - individual items in an order"""
    __tablename__ = 'order_items'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(Numeric(10, 2), nullable=False)
    total_price = db.Column(Numeric(10, 2), nullable=False)
    
    # Final weight for weight-based products (set during pickup)
    final_weight = db.Column(Numeric(10, 3), nullable=True)  # Weight in lb

    # Variant selection (snapshot at order time)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True, index=True)
    variant_name = db.Column(db.String(255), nullable=True)
    variant_price_delta = db.Column(Numeric(10, 2), nullable=True)

    # Substitute preference and fulfillment
    accept_substitute = db.Column(db.Boolean, nullable=True)
    is_unavailable = db.Column(db.Boolean, default=False, nullable=False)
    cannot_fulfill = db.Column(db.Boolean, default=False, nullable=False)

    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    source_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    source_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=True, index=True)

    variant = db.relationship('ProductVariant', foreign_keys=[variant_id])
    source_order = db.relationship('Order', foreign_keys=[source_order_id])
    source_item = db.relationship('OrderItem', foreign_keys=[source_item_id], remote_side='OrderItem.id')

    @classmethod
    def active(cls):
        """SQLAlchemy filter: non-deleted lines."""
        return cls.deleted_at.is_(None)

    @classmethod
    def soft_delete_for_order(cls, order_id, session=None):
        """Soft-delete all active lines on an order (e.g. before replace/merge)."""
        session = session or db.session
        now = utc_now()
        return cls.query.filter(
            cls.order_id == order_id,
            cls.active(),
        ).update({'deleted_at': now}, synchronize_session=False)

    @classmethod
    def get_active(cls, item_id, order_id):
        return cls.query.filter_by(id=item_id, order_id=order_id).filter(cls.active()).first()

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'total_price': float(self.total_price) if self.total_price else None,
            'final_weight': float(self.final_weight) if self.final_weight else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant_name,
            'variant_price_delta': float(self.variant_price_delta) if self.variant_price_delta is not None else None,
            'accept_substitute': self.accept_substitute,
            'is_unavailable': self.is_unavailable,
            'cannot_fulfill': self.cannot_fulfill,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'source_order_id': self.source_order_id,
            'source_item_id': self.source_item_id,
        })
        return data

