from models.base import BaseModel
from models import db
from sqlalchemy import Numeric
from sqlalchemy.dialects.mysql import JSON


class CreditTransaction(BaseModel):
    """Immutable log of every store credit balance change."""
    __tablename__ = 'credit_transactions'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    delta = db.Column(Numeric(10, 2), nullable=False)
    balance_after = db.Column(Numeric(10, 2), nullable=False)
    tx_type = db.Column(db.String(50), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=True)
    metadata_json = db.Column('metadata', JSON, nullable=True)
    created_by_admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    related_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    # Intentionally no FK — avoids circular create order with referral_records
    related_referral_id = db.Column(db.Integer, nullable=True, index=True)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self, include_user=False):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'delta': float(self.delta) if self.delta is not None else None,
            'balance_after': float(self.balance_after) if self.balance_after is not None else None,
            'tx_type': self.tx_type,
            'reason': self.reason,
            'metadata': self.metadata_json,
            'created_by_admin_user_id': self.created_by_admin_user_id,
            'related_order_id': self.related_order_id,
            'related_referral_id': self.related_referral_id,
        })
        if include_user and self.user:
            data['user'] = self.user.to_credit_tx_summary_dict()
        return data
