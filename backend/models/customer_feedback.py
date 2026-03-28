from models.base import BaseModel
from models import db


class FeedbackContext:
    """Source screen / program (filter in UI and SQL)."""
    AFTER_SALES_FIRST_ORDER = 'after_sales_first_order'
    AFTER_SALES_CHURNED = 'after_sales_churned'

    @classmethod
    def all_values(cls):
        return [cls.AFTER_SALES_FIRST_ORDER, cls.AFTER_SALES_CHURNED]


class FeedbackOutcome:
    """Outcome of one logged interaction (stored as short Chinese labels)."""
    NO_FOLLOW = '不跟进'
    FOLLOW_AGAIN = '再次跟进'
    NO_REPLY = '未回复'
    NOT_CONTACTED = '未联系'

    @classmethod
    def all_values(cls):
        return [cls.NO_FOLLOW, cls.FOLLOW_AGAIN, cls.NO_REPLY, cls.NOT_CONTACTED]


class CustomerFeedback(BaseModel):
    """
    Customer feedback log: one row per entry. Join on user_id to count how many
    entries exist per customer; zero rows means none yet.
    """
    __tablename__ = 'customer_feedback'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    context = db.Column(db.String(64), nullable=True, index=True)
    outcome = db.Column(db.String(32), nullable=False, default=FeedbackOutcome.NOT_CONTACTED)
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref(
        'feedback_records', lazy='dynamic'
    ))
    order = db.relationship('Order', foreign_keys=[order_id])
    created_by = db.relationship('User', foreign_keys=[created_by_user_id])

    def to_dict(self, include_created_by=False):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'order_id': self.order_id,
            'context': self.context,
            'outcome': self.outcome,
            'notes': self.notes,
            'created_by_user_id': self.created_by_user_id,
        })
        if include_created_by and self.created_by:
            data['created_by'] = {
                'id': self.created_by.id,
                'nickname': self.created_by.nickname,
                'phone': self.created_by.phone,
            }
        return data
