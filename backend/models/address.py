from models.base import BaseModel
from models import db

class Address(BaseModel):
    """Address model - users can have multiple addresses for delivery"""
    __tablename__ = 'addresses'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Address fields
    recipient_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), default='Canada', nullable=False)
    
    # Optional: delivery instructions
    delivery_instructions = db.Column(db.Text, nullable=True)
    
    # Default address flag
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'recipient_name': self.recipient_name,
            'phone': self.phone,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'province': self.province,
            'postal_code': self.postal_code,
            'country': self.country,
            'delivery_instructions': self.delivery_instructions,
            'is_default': self.is_default
        })
        return data

