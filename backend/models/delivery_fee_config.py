from models.base import BaseModel
from models import db
from sqlalchemy import JSON

class DeliveryFeeConfig(BaseModel):
    """Delivery fee configuration model with dynamic tiers"""
    __tablename__ = 'delivery_fee_configs'
    
    # Tiers stored as JSON array
    # Structure: [
    #   {"threshold": 0, "fee": 7.99},        # Base fee (threshold 0 means default)
    #   {"threshold": 58.00, "fee": 5.99},    # First threshold
    #   {"threshold": 128.00, "fee": 3.99},   # Second threshold
    #   {"threshold": 150.00, "fee": 0}       # Free shipping threshold
    # ]
    # Tiers must be sorted by threshold in ascending order
    tiers = db.Column(JSON, nullable=False, default=[
        {"threshold": 0, "fee": 7.99},
        {"threshold": 58.00, "fee": 5.99},
        {"threshold": 128.00, "fee": 3.99},
        {"threshold": 150.00, "fee": 0}
    ])
    
    # Active flag - only one config should be active at a time
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'tiers': self.tiers if self.tiers else [],
            'is_active': self.is_active
        })
        return data
