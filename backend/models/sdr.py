from models.base import BaseModel
from models import db
from sqlalchemy import Numeric

class SDR(BaseModel):
    """Sales Development Representative model"""
    __tablename__ = 'sdrs'
    
    # SDR info
    name = db.Column(db.String(255), nullable=False)  # e.g., "花泽"
    source_identifier = db.Column(db.String(50), unique=True, nullable=False, index=True)  # matches user_source
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    commission_rules = db.relationship('CommissionRule', backref='sdr', lazy=True, cascade='all, delete-orphan')
    commission_records = db.relationship('CommissionRecord', backref='sdr', lazy=True)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'source_identifier': self.source_identifier,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active
        })
        return data


class CommissionRule(BaseModel):
    """Commission rules: fixed amount per item/weight for each product"""
    __tablename__ = 'commission_rules'
    
    sdr_id = db.Column(db.Integer, db.ForeignKey('sdrs.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    # Commission type: 'per_item' or 'per_weight'
    # This allows flexibility - weight-based products can still have per-item commission
    commission_type = db.Column(db.String(20), default='per_item', nullable=False)  # 'per_item' or 'per_weight'
    
    # Fixed commission amounts (in dollars)
    # If commission_type is 'per_item': amount per item
    # If commission_type is 'per_weight': amount per lb/unit
    own_customer_amount = db.Column(Numeric(10, 2), nullable=False)  # e.g., 6.00 for 水鸭 (own customer)
    general_customer_amount = db.Column(Numeric(10, 2), nullable=False)  # e.g., 1.50 for 水鸭 (general customer)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='commission_rules')
    
    # Unique constraint: one rule per SDR per product
    __table_args__ = (
        db.UniqueConstraint('sdr_id', 'product_id', name='uq_sdr_product'),
    )
    
    def to_dict(self, include_product=False):
        data = super().to_dict()
        data.update({
            'sdr_id': self.sdr_id,
            'product_id': self.product_id,
            'commission_type': self.commission_type,
            'own_customer_amount': float(self.own_customer_amount) if self.own_customer_amount else None,
            'general_customer_amount': float(self.general_customer_amount) if self.general_customer_amount else None,
            'is_active': self.is_active
        })
        
        if include_product and self.product:
            data['product'] = self.product.to_dict()
        
        return data


class CommissionRecord(BaseModel):
    """Commission summary per group deal per SDR"""
    __tablename__ = 'commission_records'
    
    group_deal_id = db.Column(db.Integer, db.ForeignKey('group_deals.id'), nullable=False, index=True)
    sdr_id = db.Column(db.Integer, db.ForeignKey('sdrs.id'), nullable=False, index=True)
    
    # Totals
    total_commission = db.Column(Numeric(10, 2), nullable=False)
    own_customer_commission = db.Column(Numeric(10, 2), default=0, nullable=False)
    general_customer_commission = db.Column(Numeric(10, 2), default=0, nullable=False)
    
    # Manual adjustment (can be positive or negative)
    manual_adjustment = db.Column(Numeric(10, 2), default=0, nullable=False)
    adjustment_notes = db.Column(db.Text, nullable=True)
    
    # Detailed breakdown (JSON)
    # Structure: [
    #   {
    #     "product_id": 1,
    #     "product_name": "水鸭",
    #     "pricing_type": "per_item",
    #     "own_quantity": 30,
    #     "general_quantity": 15,
    #     "own_weight": null,
    #     "general_weight": null,
    #     "own_commission": 180.00,
    #     "general_commission": 22.50,
    #     "total_commission": 202.50,
    #     "own_rate": 6.00,
    #     "general_rate": 1.50
    #   },
    #   ...
    # ]
    details = db.Column(db.JSON, nullable=True)
    
    # Payment tracking
    payment_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, paid, cancelled
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    group_deal = db.relationship('GroupDeal', backref='commission_records')
    
    # Unique constraint: one record per group deal per SDR
    __table_args__ = (
        db.UniqueConstraint('group_deal_id', 'sdr_id', name='uq_groupdeal_sdr'),
    )
    
    def to_dict(self, include_relations=False):
        data = super().to_dict()
        
        # Calculate final total with manual adjustment
        # Convert Decimal to float to avoid type errors
        base_total = float(self.total_commission) if self.total_commission is not None else 0.0
        adjustment = float(self.manual_adjustment) if self.manual_adjustment is not None else 0.0
        final_total = float(base_total + adjustment)
        
        data.update({
            'group_deal_id': self.group_deal_id,
            'sdr_id': self.sdr_id,
            'total_commission': float(base_total),
            'own_customer_commission': float(self.own_customer_commission) if self.own_customer_commission is not None else None,
            'general_customer_commission': float(self.general_customer_commission) if self.general_customer_commission is not None else None,
            'manual_adjustment': float(adjustment),
            'final_total': float(final_total),
            'adjustment_notes': self.adjustment_notes,
            'details': self.details,
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_notes': self.payment_notes
        })
        
        if include_relations:
            if self.sdr:
                data['sdr'] = self.sdr.to_dict()
            if self.group_deal:
                data['group_deal'] = self.group_deal.to_dict()
        
        return data
