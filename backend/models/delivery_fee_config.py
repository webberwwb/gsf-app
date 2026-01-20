from models.base import BaseModel
from models import db
from sqlalchemy import Numeric

class DeliveryFeeConfig(BaseModel):
    """Delivery fee configuration model"""
    __tablename__ = 'delivery_fee_configs'
    
    # Base shipping fee (default: 7.99)
    base_fee = db.Column(Numeric(10, 2), nullable=False, default=7.99)
    
    # Threshold 1: subtotal >= 58, fee = 5.99
    threshold_1_amount = db.Column(Numeric(10, 2), nullable=False, default=58.00)
    threshold_1_fee = db.Column(Numeric(10, 2), nullable=False, default=5.99)
    
    # Threshold 2: subtotal >= 128, fee = 3.99
    threshold_2_amount = db.Column(Numeric(10, 2), nullable=False, default=128.00)
    threshold_2_fee = db.Column(Numeric(10, 2), nullable=False, default=3.99)
    
    # Threshold 3: subtotal >= 150, free delivery (fee = 0)
    threshold_3_amount = db.Column(Numeric(10, 2), nullable=False, default=150.00)
    
    # Active flag - only one config should be active at a time
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'base_fee': float(self.base_fee) if self.base_fee else None,
            'threshold_1_amount': float(self.threshold_1_amount) if self.threshold_1_amount else None,
            'threshold_1_fee': float(self.threshold_1_fee) if self.threshold_1_fee else None,
            'threshold_2_amount': float(self.threshold_2_amount) if self.threshold_2_amount else None,
            'threshold_2_fee': float(self.threshold_2_fee) if self.threshold_2_fee else None,
            'threshold_3_amount': float(self.threshold_3_amount) if self.threshold_3_amount else None,
            'is_active': self.is_active
        })
        return data
