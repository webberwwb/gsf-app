from models.base import BaseModel
from models import db

class Supplier(BaseModel):
    """Supplier model"""
    __tablename__ = 'suppliers'
    
    name = db.Column(db.String(255), nullable=False, index=True)
    contact_person = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'notes': self.notes,
            'is_active': self.is_active
        })
        return data






