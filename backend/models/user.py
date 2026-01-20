from models.base import BaseModel
from models import db
from datetime import datetime, timezone
from models.base import utc_now
from constants.status_enums import UserStatus

class User(BaseModel):
    """User model"""
    __tablename__ = 'users'
    
    # Required: phone number (nullable for WeChat-only users, but required for phone auth)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    
    # Optional: nickname
    nickname = db.Column(db.String(255), nullable=True)
    
    # Points: default 0, accumulate 1 point per dollar spent
    points = db.Column(db.Integer, default=0, nullable=False)
    
    # Dates
    creation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_date = db.Column(db.DateTime, nullable=True)
    
    # Status (see constants.status_enums.UserStatus for valid values)
    status = db.Column(db.String(20), default=UserStatus.ACTIVE.value, nullable=False)
    
    # Optional: email
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    
    # WeChat info (optional)
    wechat_openid = db.Column(db.String(128), unique=True, nullable=True, index=True)
    wechat_unionid = db.Column(db.String(128), nullable=True, index=True)
    wechat_nickname = db.Column(db.String(255), nullable=True)
    wechat_avatar = db.Column(db.String(512), nullable=True)
    
    # WhatsApp info (optional)
    whatsapp_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    whatsapp_verified = db.Column(db.Boolean, default=False)
    
    # WeChat ID for group buying (required for users)
    wechat = db.Column(db.String(255), nullable=True)
    
    # User source (e.g., "花泽", "default")
    user_source = db.Column(db.String(50), nullable=True, default='default')
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)
    tokens = db.relationship('AuthToken', backref='user', lazy=True, cascade='all, delete-orphan')
    roles = db.relationship('UserRole', backref='user', lazy=True, cascade='all, delete-orphan')
    
    @property
    def is_active(self):
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE.value
    
    @property
    def is_admin(self):
        """Check if user has admin role"""
        return any(role.role == 'admin' for role in self.roles)
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        return any(role.role == role_name for role in self.roles)
    
    def get_roles(self):
        """Get list of role names"""
        return [role.role for role in self.roles]
    
    @property
    def order_count(self):
        """Get count of orders for this user"""
        return len(self.orders) if self.orders else 0
    
    def to_dict(self, include_order_count=False):
        data = super().to_dict()
        data.update({
            'phone': self.phone,
            'nickname': self.nickname,
            'points': self.points,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_login_date': self.last_login_date.isoformat() if self.last_login_date else None,
            'status': self.status,
            'email': self.email,
            'wechat': self.wechat,
            'user_source': self.user_source or 'default',
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'roles': self.get_roles()
        })
        
        if include_order_count:
            data['order_count'] = self.order_count
        
        return data

class AuthToken(BaseModel):
    """Authentication token model for bearer token validation"""
    __tablename__ = 'auth_tokens'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(50), default='bearer')  # bearer, wechat, whatsapp
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    
    def is_valid(self):
        """Check if token is valid"""
        if self.is_revoked:
            return False
        
        # All datetimes are stored as naive UTC in database
        now = utc_now()
        expires = self.expires_at
        
        return now < expires
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'token': self.token[:10] + '...',  # Don't expose full token
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_revoked': self.is_revoked
        })
        return data

class UserRole(BaseModel):
    """User role model for role-based access control"""
    __tablename__ = 'user_roles'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'user', 'moderator', etc.
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'role': self.role
        })
        return data
