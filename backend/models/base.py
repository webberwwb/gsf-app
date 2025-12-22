from models import db
from datetime import datetime, timezone

def utc_now():
    """Return current UTC time as naive datetime (for MySQL compatibility)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Example model - you can add your business models here
# class YourModel(BaseModel):
#     __tablename__ = 'your_table'
#     
#     name = db.Column(db.String(255), nullable=False)
#     description = db.Column(db.Text)
#     
#     def to_dict(self):
#         data = super().to_dict()
#         data.update({
#             'name': self.name,
#             'description': self.description
#         })
#         return data

