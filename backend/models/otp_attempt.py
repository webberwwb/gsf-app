from models.base import BaseModel
from models import db
from datetime import datetime

class OTPAttempt(BaseModel):
    """OTP attempt tracking model for Twilio usage monitoring"""
    __tablename__ = 'otp_attempts'
    
    # Phone number that received OTP
    phone = db.Column(db.String(20), nullable=False, index=True)
    
    # OTP action type
    action_type = db.Column(db.String(20), nullable=False, default='send')  # 'send' or 'verify'
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'success', 'failed'
    
    # Twilio-specific fields
    twilio_status = db.Column(db.String(50), nullable=True)  # Twilio verification status
    twilio_sid = db.Column(db.String(100), nullable=True, index=True)  # Twilio verification SID
    twilio_error_code = db.Column(db.String(20), nullable=True)  # Twilio error code if failed
    twilio_error_message = db.Column(db.String(500), nullable=True)  # Twilio error message
    
    # Channel used (always 'sms' for now)
    channel = db.Column(db.String(20), nullable=False, default='sms')
    
    # Cost tracking (estimated cost per SMS in USD)
    estimated_cost = db.Column(db.Numeric(10, 6), nullable=True, default=0.0075)  # ~$0.0075 per SMS
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # User ID if verified successfully (for linking attempts to users)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'phone': self.phone,
            'action_type': self.action_type,
            'status': self.status,
            'twilio_status': self.twilio_status,
            'twilio_sid': self.twilio_sid,
            'twilio_error_code': self.twilio_error_code,
            'twilio_error_message': self.twilio_error_message,
            'channel': self.channel,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }

