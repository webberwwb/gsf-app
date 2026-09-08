from models.base import BaseModel
from models import db
from sqlalchemy import Numeric


PAYOUT_CREDIT = 'credit'
PAYOUT_CASH = 'cash'

STATUS_CREDITED = 'credited'
STATUS_PAYABLE = 'payable'
STATUS_PAID = 'paid'
STATUS_REVERSED = 'reversed'

COMMISSION_PER_ITEM = 'per_item'
COMMISSION_PER_WEIGHT = 'per_weight'


class InfluencerProfile(BaseModel):
    """One profile per 推荐官 user."""
    __tablename__ = 'influencer_profiles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    payout_type = db.Column(db.String(20), nullable=False, default=PAYOUT_CREDIT)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    commission_from_group_deal_id = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self, include_user=False):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'payout_type': self.payout_type,
            'is_active': self.is_active,
            'commission_from_group_deal_id': self.commission_from_group_deal_id,
        })
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'nickname': self.user.nickname,
                'phone': self.user.phone,
                'wechat': self.user.wechat,
                'referral_code': self.user.referral_code,
            }
        return data


class InfluencerProgramConfig(BaseModel):
    """Singleton-style config (use is_active=True)."""
    __tablename__ = 'influencer_program_configs'

    lead_bonus_amount = db.Column(Numeric(10, 2), nullable=False, default=5)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'lead_bonus_amount': float(self.lead_bonus_amount) if self.lead_bonus_amount is not None else 0,
            'is_active': self.is_active,
        })
        return data


class InfluencerProductRate(BaseModel):
    """Global default commission per product."""
    __tablename__ = 'influencer_product_rates'

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, unique=True, index=True)
    commission_type = db.Column(db.String(20), nullable=False, default=COMMISSION_PER_ITEM)
    amount = db.Column(Numeric(10, 2), nullable=False, default=0)

    product = db.relationship('Product')

    def to_dict(self, include_product=False):
        data = super().to_dict()
        data.update({
            'product_id': self.product_id,
            'commission_type': self.commission_type,
            'amount': float(self.amount) if self.amount is not None else 0,
        })
        if include_product and self.product:
            data['product'] = {
                'id': self.product.id,
                'name': self.product.name,
                'pricing_type': self.product.pricing_type,
            }
        return data


class InfluencerRateOverride(BaseModel):
    """Per-推荐官 product rate override."""
    __tablename__ = 'influencer_rate_overrides'

    influencer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    commission_type = db.Column(db.String(20), nullable=False, default=COMMISSION_PER_ITEM)
    amount = db.Column(Numeric(10, 2), nullable=False, default=0)

    product = db.relationship('Product')

    __table_args__ = (
        db.UniqueConstraint('influencer_user_id', 'product_id', name='uq_influencer_product_override'),
    )

    def to_dict(self, include_product=False):
        data = super().to_dict()
        data.update({
            'influencer_user_id': self.influencer_user_id,
            'product_id': self.product_id,
            'commission_type': self.commission_type,
            'amount': float(self.amount) if self.amount is not None else 0,
        })
        if include_product and self.product:
            data['product'] = {
                'id': self.product.id,
                'name': self.product.name,
                'pricing_type': self.product.pricing_type,
            }
        return data


class InfluencerCommissionEntry(BaseModel):
    """One commission row per paid order (idempotent)."""
    __tablename__ = 'influencer_commission_entries'

    influencer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    customer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True, index=True)
    amount = db.Column(Numeric(10, 2), nullable=False, default=0)
    payout_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, index=True)
    details = db.Column(db.JSON, nullable=True)
    credit_transaction_id = db.Column(db.Integer, db.ForeignKey('credit_transactions.id'), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    paid_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    order = db.relationship('Order')

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'influencer_user_id': self.influencer_user_id,
            'customer_user_id': self.customer_user_id,
            'order_id': self.order_id,
            'amount': float(self.amount) if self.amount is not None else 0,
            'payout_type': self.payout_type,
            'status': self.status,
            'details': self.details,
            'credit_transaction_id': self.credit_transaction_id,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'paid_by_admin_id': self.paid_by_admin_id,
            'notes': self.notes,
        })
        return data
