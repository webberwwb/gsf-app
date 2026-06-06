"""Audit trail for order lifecycle (merge, item replacements)."""
from sqlalchemy import JSON
from models.base import BaseModel
from models import db


class OrderAuditEvent(BaseModel):
    __tablename__ = 'order_audit_events'

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    payload = db.Column(JSON, nullable=False)

    order = db.relationship('Order', foreign_keys=[order_id], backref='audit_events')
    actor = db.relationship('User', foreign_keys=[actor_user_id])

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'order_id': self.order_id,
            'event_type': self.event_type,
            'actor_user_id': self.actor_user_id,
            'payload': self.payload,
        })
        return data
