from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, time

from sqlalchemy import Numeric

from models import db
from models.base import BaseModel


def elapsed_minutes(start, end, *, strict=False):
    """Whole minutes between two times. Used for 时薪 × (分钟 / 60)."""
    if start is None or end is None:
        if strict:
            raise ValueError('结束时间必须晚于开始时间')
        return None
    start_dt = datetime.combine(date.today(), start)
    end_dt = datetime.combine(date.today(), end)
    if end_dt <= start_dt:
        if strict:
            raise ValueError('结束时间必须晚于开始时间')
        return None
    seconds = Decimal(str((end_dt - start_dt).total_seconds()))
    return (seconds / Decimal('60')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


class FulfillmentProfile(BaseModel):
    """Pay rates for a 配货员."""
    __tablename__ = 'fulfillment_profiles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    hourly_rate = db.Column(Numeric(10, 2), nullable=False, default=0)
    delivery_fee_per_order = db.Column(Numeric(10, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate is not None else 0.0,
            'delivery_fee_per_order': float(self.delivery_fee_per_order) if self.delivery_fee_per_order is not None else 0.0,
            'is_active': bool(self.is_active),
        })
        if self.user:
            data['user'] = {
                'id': self.user.id,
                'nickname': self.user.nickname,
                'email': self.user.email,
            }
        return data


class FulfillmentWorkSession(BaseModel):
    """Packing timesheet row (e.g. Saturday 16:00–19:00)."""
    __tablename__ = 'fulfillment_work_sessions'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    work_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    hours = db.Column(Numeric(6, 2), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    group_deal_id = db.Column(db.Integer, db.ForeignKey('group_deals.id'), nullable=True)
    hourly_rate_snapshot = db.Column(Numeric(10, 2), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])

    @property
    def minutes(self):
        return elapsed_minutes(self.start_time, self.end_time)

    @property
    def labor_amount(self):
        minutes = self.minutes
        if minutes is None or self.hourly_rate_snapshot is None:
            return Decimal('0')
        rate = Decimal(str(self.hourly_rate_snapshot))
        return (rate * minutes / Decimal('60')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def to_dict(self):
        data = super().to_dict()
        work_date = self.work_date.isoformat() if isinstance(self.work_date, date) else self.work_date
        start = self.start_time.strftime('%H:%M') if isinstance(self.start_time, time) else self.start_time
        end = self.end_time.strftime('%H:%M') if isinstance(self.end_time, time) else self.end_time
        data.update({
            'user_id': self.user_id,
            'work_date': work_date,
            'start_time': start,
            'end_time': end,
            'hours': float(self.hours) if self.hours is not None else None,
            'minutes': int(self.minutes) if self.minutes is not None else None,
            'notes': self.notes,
            'group_deal_id': self.group_deal_id,
            'hourly_rate_snapshot': float(self.hourly_rate_snapshot) if self.hourly_rate_snapshot is not None else None,
            'labor_amount': float(self.labor_amount),
            'created_by_user_id': self.created_by_user_id,
            'updated_by_user_id': self.updated_by_user_id,
            'is_open': self.end_time is None,
        })
        if self.user:
            data['user'] = {
                'id': self.user.id,
                'nickname': self.user.nickname,
                'email': self.user.email,
            }
        return data


class FulfillmentPayout(BaseModel):
    """Admin-recorded payment to a 配货员."""
    __tablename__ = 'fulfillment_payouts'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(Numeric(10, 2), nullable=False)
    paid_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    paid_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        data = super().to_dict()
        paid_at = self.paid_at.isoformat() if isinstance(self.paid_at, datetime) else self.paid_at
        data.update({
            'user_id': self.user_id,
            'amount': float(self.amount) if self.amount is not None else 0.0,
            'paid_at': paid_at,
            'notes': self.notes,
            'paid_by_user_id': self.paid_by_user_id,
        })
        if self.user:
            data['user'] = {
                'id': self.user.id,
                'nickname': self.user.nickname,
                'email': self.user.email,
            }
        return data
