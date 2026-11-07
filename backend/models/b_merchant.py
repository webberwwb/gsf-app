"""Wholesale (B端) merchants and delivery sheets."""
from models.base import BaseModel
from models import db
from sqlalchemy import JSON, Numeric
from utils.money import round_money_float

SUPPLIER_NAME = '15891779 Canada Inc. (Grain Story Farm)'
DEFAULT_PAYMENT_TERMS = (
    'Certified Cheque to 15891779 Canada Inc., Payment due within 1 week / 一周内支付'
)
DEFAULT_PAYMENT_DUE_DAYS = 7


def _money(value):
    if value is None:
        return None
    return round_money_float(value)


class BMerchant(BaseModel):
    """收货方. Separate from catalog suppliers."""
    __tablename__ = 'b_merchants'

    name = db.Column(db.String(255), nullable=False, index=True)
    contact_person = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(64), nullable=True)
    address = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    show_prices = db.Column(db.Boolean, default=True, nullable=False)
    payment_terms = db.Column(db.Text, nullable=False, default=DEFAULT_PAYMENT_TERMS)
    payment_due_days = db.Column(db.Integer, nullable=False, default=DEFAULT_PAYMENT_DUE_DAYS)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    deliveries = db.relationship('BDelivery', back_populates='merchant', lazy=True)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'address': self.address,
            'notes': self.notes,
            'show_prices': bool(self.show_prices),
            'payment_terms': self.payment_terms,
            'payment_due_days': self.payment_due_days,
            'is_active': bool(self.is_active),
        })
        return data


class BDelivery(BaseModel):
    """One printed delivery sheet and its signed-paper / payment record."""
    __tablename__ = 'b_deliveries'

    merchant_id = db.Column(db.Integer, db.ForeignKey('b_merchants.id'), nullable=False, index=True)
    merchant = db.relationship('BMerchant', back_populates='deliveries')

    invoice_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=False)
    payment_terms = db.Column(db.Text, nullable=False)
    show_prices = db.Column(db.Boolean, default=True, nullable=False)

    subtotal = db.Column(Numeric(10, 2), nullable=False, default=0)
    hst = db.Column(Numeric(10, 2), nullable=False, default=0)
    discount = db.Column(Numeric(10, 2), nullable=False, default=0)
    grand_total = db.Column(Numeric(10, 2), nullable=False, default=0)

    payment_status = db.Column(db.String(20), nullable=False, default='unpaid', index=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    signature_images = db.Column(JSON, nullable=True)
    check_images = db.Column(JSON, nullable=True)

    lines = db.relationship(
        'BDeliveryLine',
        back_populates='delivery',
        cascade='all, delete-orphan',
        order_by='BDeliveryLine.sort_order',
        lazy=True,
    )

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'merchant_id': self.merchant_id,
            'merchant_name': self.merchant.name if self.merchant else None,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'payment_terms': self.payment_terms,
            'show_prices': bool(self.show_prices),
            'subtotal': _money(self.subtotal),
            'hst': _money(self.hst),
            'discount': _money(self.discount),
            'grand_total': _money(self.grand_total),
            'payment_status': self.payment_status,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'notes': self.notes,
            'signature_images': self.signature_images or [],
            'check_images': self.check_images or [],
            'lines': [line.to_dict() for line in self.lines],
        })
        return data


class BDeliveryLine(BaseModel):
    """Snapshotted line. Prices stay stored when the sheet hides them."""
    __tablename__ = 'b_delivery_lines'

    delivery_id = db.Column(db.Integer, db.ForeignKey('b_deliveries.id'), nullable=False, index=True)
    delivery = db.relationship('BDelivery', back_populates='lines')

    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True, index=True)
    product_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(32), nullable=False, default='pc')
    unit_price = db.Column(Numeric(10, 2), nullable=False, default=0)
    amount = db.Column(Numeric(10, 2), nullable=False, default=0)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'delivery_id': self.delivery_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': _money(self.quantity),
            'unit': self.unit,
            'unit_price': _money(self.unit_price),
            'amount': _money(self.amount),
            'sort_order': self.sort_order,
        })
        return data
