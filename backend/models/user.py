from models.base import BaseModel
from models import db
from datetime import datetime, timezone
from models.base import utc_now
from constants.status_enums import UserStatus
from sqlalchemy import Numeric

class User(BaseModel):
    """User model"""
    __tablename__ = 'users'
    
    # Required: phone number (nullable for WeChat-only users, but required for phone auth)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    
    # Optional: nickname
    nickname = db.Column(db.String(255), nullable=True)
    
    # Points: default 0, accumulate via orders (loyalty); separate from store credit
    points = db.Column(db.Integer, default=0, nullable=False)

    # Store credit (CAD) — checkout / referrals / admin
    store_credit_balance = db.Column(Numeric(10, 2), default=0, nullable=False)

    # Referrals (code assigned after first completed order)
    referral_code = db.Column(db.String(32), unique=True, nullable=True, index=True)
    referred_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
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

    # Stripe customer + saved payment method (IDs only; never store PAN)
    stripe_customer_id = db.Column(db.String(255), nullable=True, index=True)
    stripe_payment_method_id = db.Column(db.String(255), nullable=True)
    stripe_card_brand = db.Column(db.String(32), nullable=True)
    stripe_card_last4 = db.Column(db.String(4), nullable=True)
    
    # User source (e.g., "花泽", "default")
    user_source = db.Column(db.String(50), nullable=True, default='default')
    
    # Self-referential referrer
    referrer = db.relationship(
        'User',
        remote_side='User.id',
        foreign_keys=[referred_by_user_id],
        backref=db.backref('referred_users', lazy='dynamic'),
    )
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
    
    def to_dict(self, include_order_count=False, include_referrer=False):
        data = super().to_dict()
        data.update({
            'phone': self.phone,
            'nickname': self.nickname,
            'points': self.points,
            'store_credit_balance': float(self.store_credit_balance) if self.store_credit_balance is not None else 0.0,
            'referral_code': self.referral_code,
            'referral_unlocked': bool(self.referral_code),
            'referred_by_user_id': self.referred_by_user_id,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_login_date': self.last_login_date.isoformat() if self.last_login_date else None,
            'status': self.status,
            'email': self.email,
            'has_card_on_file': bool(self.stripe_payment_method_id),
            'stripe_card_brand': self.stripe_card_brand,
            'stripe_card_last4': self.stripe_card_last4,
            'wechat': self.wechat,
            'user_source': self.user_source or 'default',
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'roles': self.get_roles()
        })

        if include_referrer and self.referred_by_user_id:
            inv = self.referrer
            if inv:
                data['referrer_display_name'] = inv.nickname or inv.phone or f'用户{inv.id}'
            else:
                data['referrer_display_name'] = None
        elif include_referrer:
            data['referrer_display_name'] = None
        
        if include_order_count:
            data['order_count'] = self.order_count
        
        return data

    def to_credit_tx_summary_dict(self):
        """Minimal user fields for admin credit transaction lists."""
        return {
            'id': self.id,
            'nickname': self.nickname,
            'phone': self.phone,
            'wechat': self.wechat,
            'wechat_nickname': self.wechat_nickname,
            'email': self.email,
        }


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
    role = db.Column(db.String(50), nullable=False)  # 'admin', 'user'
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'role': self.role
        })
        return data
