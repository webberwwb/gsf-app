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
    
    # Map center (not used for fees). Region groups are stored in distance_surcharges:
    # [{"label": "...", "surcharge": 4, "cities": ["Waterloo", ...]}]
    depot = db.Column(JSON, nullable=True)
    distance_surcharges = db.Column(JSON, nullable=True)
    beyond_surcharge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    beyond_label = db.Column(db.String(255), nullable=True)

    # Active flag - only one config should be active at a time
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        from utils.shipping import region_surcharges_from

        data = super().to_dict()
        data.update({
            'tiers': self.tiers if self.tiers else [],
            'depot': self.depot,
            'region_surcharges': region_surcharges_from(self),
            'distance_surcharges': [],
            'beyond_surcharge': 0,
            'beyond_label': '',
            'is_active': self.is_active
        })
        return data
