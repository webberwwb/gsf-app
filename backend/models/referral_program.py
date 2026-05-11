from models.base import BaseModel
from models import db
from sqlalchemy import Numeric


class ReferralProgramConfig(BaseModel):
    """Singleton-style config row (use is_active=True)."""
    __tablename__ = 'referral_program_configs'

    invitee_bonus_amount = db.Column(Numeric(10, 2), nullable=False, default=5)
    inviter_reward_amount = db.Column(Numeric(10, 2), nullable=False, default=5)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'invitee_bonus_amount': float(self.invitee_bonus_amount) if self.invitee_bonus_amount is not None else 0,
            'inviter_reward_amount': float(self.inviter_reward_amount) if self.inviter_reward_amount is not None else 0,
            'is_active': self.is_active,
        })
        return data


class ReferralRecord(BaseModel):
    """One row per invite relationship (invitee can only have one)."""
    __tablename__ = 'referral_records'

    STATUS_PENDING_ORDER = 'pending_order'
    STATUS_REWARDED = 'rewarded'

    inviter_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invitee_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    status = db.Column(db.String(32), nullable=False, default=STATUS_PENDING_ORDER, index=True)

    invitee_bonus_transaction_id = db.Column(db.Integer, db.ForeignKey('credit_transactions.id'), nullable=True)
    inviter_reward_transaction_id = db.Column(db.Integer, db.ForeignKey('credit_transactions.id'), nullable=True)
    first_completed_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    rewarded_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'inviter_user_id': self.inviter_user_id,
            'invitee_user_id': self.invitee_user_id,
            'status': self.status,
            'invitee_bonus_transaction_id': self.invitee_bonus_transaction_id,
            'inviter_reward_transaction_id': self.inviter_reward_transaction_id,
            'first_completed_order_id': self.first_completed_order_id,
            'rewarded_at': self.rewarded_at.isoformat() if self.rewarded_at else None,
        })
        return data
