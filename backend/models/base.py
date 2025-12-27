from models import db
from datetime import datetime
from zoneinfo import ZoneInfo

def est_now():
    """Return current EST time as naive datetime (for MySQL compatibility)"""
    # EST/EDT timezone (Eastern Time)
    return datetime.now(ZoneInfo('America/New_York')).replace(tzinfo=None)

# Alias for backwards compatibility
utc_now = est_now

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=est_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=est_now, onupdate=est_now, nullable=False)
    
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

