"""Admin routes for B端 merchants and delivery sheets."""
from datetime import datetime, date

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.orm import selectinload

from models import db
from models.base import est_now
from models.b_merchant import (
    DEFAULT_PAYMENT_DUE_DAYS,
    DEFAULT_PAYMENT_TERMS,
    BDelivery,
    BDeliveryLine,
    BMerchant,
)
from models.product import Product
from routes.admin import require_admin_auth
from utils.money import round_money

b_merchants_bp = Blueprint('b_merchants', __name__)

MAX_IMAGES = 8


def _auth():
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return None, error_response, status_code
    return user_id, None, None


def _bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_date(value, field):
    if not value:
        raise ValueError(f'{field} is required')
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValueError(f'{field} must be YYYY-MM-DD') from exc


def _money_field(value, field, allow_negative=False):
    try:
        amount = round_money(0 if value in (None, '') else value)
    except Exception as exc:
        raise ValueError(f'{field} is not a number') from exc
    if not allow_negative and amount < 0:
        raise ValueError(f'{field} cannot be negative')
    return amount


def _image_list(value, field):
    if value in (None, ''):
        return []
    if not isinstance(value, list):
        raise ValueError(f'{field} must be a list')
    if len(value) > MAX_IMAGES:
        raise ValueError(f'{field} allows at most {MAX_IMAGES} images')
    urls = []
    for item in value:
        url = _text(item)
        if not url:
            continue
        if len(url) > 1024:
            raise ValueError(f'{field} URL is too long')
        urls.append(url)
    return urls


def _apply_merchant(merchant, data, partial):
    if not partial or 'name' in data:
        name = _text(data.get('name'))
        if not name:
            raise ValueError('name is required')
        merchant.name = name[:255]
    if not partial or 'contact_person' in data:
        merchant.contact_person = (_text(data.get('contact_person')) or None)
        if merchant.contact_person:
            merchant.contact_person = merchant.contact_person[:255]
    if not partial or 'phone' in data:
        phone = _text(data.get('phone'))
        merchant.phone = phone[:64] if phone else None
    if not partial or 'address' in data:
        merchant.address = _text(data.get('address'))
    if not partial or 'notes' in data:
        merchant.notes = _text(data.get('notes'))
    if not partial or 'show_prices' in data:
        merchant.show_prices = _bool(data.get('show_prices'), True)
    if not partial or 'payment_terms' in data:
        terms = _text(data.get('payment_terms')) or DEFAULT_PAYMENT_TERMS
        merchant.payment_terms = terms
    if not partial or 'payment_due_days' in data:
        raw_days = data.get('payment_due_days', DEFAULT_PAYMENT_DUE_DAYS)
        try:
            days = int(raw_days)
        except (TypeError, ValueError) as exc:
            raise ValueError('payment_due_days must be a whole number') from exc
        if days < 0 or days > 365:
            raise ValueError('payment_due_days must be between 0 and 365')
        merchant.payment_due_days = days
    if not partial or 'is_active' in data:
        merchant.is_active = _bool(data.get('is_active'), True)


def _apply_lines(delivery, raw_lines):
    if not isinstance(raw_lines, list) or not raw_lines:
        raise ValueError('At least one product line is required')
    product_ids = []
    for raw in raw_lines:
        if isinstance(raw, dict) and raw.get('product_id'):
            product_ids.append(int(raw['product_id']))
    products = {}
    if product_ids:
        products = {
            product.id: product
            for product in Product.query.filter(Product.id.in_(product_ids)).all()
        }
    delivery.lines.clear()
    db.session.flush()
    subtotal = round_money(0)
    for index, raw in enumerate(raw_lines):
        if not isinstance(raw, dict):
            raise ValueError('Each line must be an object')
        product_id = raw.get('product_id') or None
        product = None
        if product_id:
            product = products.get(int(product_id))
            if not product:
                raise ValueError('Product not found')
            product_id = product.id
        name = _text(raw.get('product_name')) or (product.name if product else None)
        if not name:
            raise ValueError('product_name is required')
        quantity = _money_field(raw.get('quantity'), 'quantity')
        if quantity <= 0:
            raise ValueError('quantity must be greater than 0')
        unit = _text(raw.get('unit')) or 'pc'
        unit_price = _money_field(raw.get('unit_price', 0), 'unit_price')
        amount = round_money(quantity * unit_price)
        subtotal += amount
        delivery.lines.append(BDeliveryLine(
            product_id=product_id,
            product_name=name[:255],
            quantity=quantity,
            unit=unit[:32],
            unit_price=unit_price,
            amount=amount,
            sort_order=index,
        ))
    return subtotal


def _apply_delivery(delivery, data):
    merchant_id = data.get('merchant_id')
    merchant = BMerchant.query.get(merchant_id) if merchant_id else None
    if not merchant:
        raise ValueError('merchant is required')
    delivery.merchant = merchant
    delivery.invoice_date = _parse_date(data.get('invoice_date'), 'invoice_date')
    delivery.due_date = _parse_date(data.get('due_date'), 'due_date')
    delivery.payment_terms = _text(data.get('payment_terms')) or merchant.payment_terms or DEFAULT_PAYMENT_TERMS
    delivery.show_prices = _bool(data.get('show_prices'), merchant.show_prices)
    subtotal = _apply_lines(delivery, data.get('lines'))
    hst = _money_field(data.get('hst', 0), 'hst')
    discount = _money_field(data.get('discount', 0), 'discount')
    delivery.subtotal = subtotal
    delivery.hst = hst
    delivery.discount = discount
    delivery.grand_total = round_money(subtotal + hst - discount)
    status = _text(data.get('payment_status')) or 'unpaid'
    if status not in ('unpaid', 'paid'):
        raise ValueError('payment_status must be unpaid or paid')
    delivery.payment_status = status
    if status == 'paid':
        if not delivery.paid_at:
            delivery.paid_at = est_now()
    else:
        delivery.paid_at = None
    if 'notes' in data:
        delivery.notes = _text(data.get('notes'))
    if 'signature_images' in data:
        delivery.signature_images = _image_list(data.get('signature_images'), 'signature_images')
    if 'check_images' in data:
        delivery.check_images = _image_list(data.get('check_images'), 'check_images')


def _delivery_query():
    return BDelivery.query.options(
        selectinload(BDelivery.merchant),
        selectinload(BDelivery.lines),
    )


def _filtered_deliveries():
    query = _delivery_query()
    merchant_id = request.args.get('merchant_id', type=int)
    if merchant_id:
        query = query.filter(BDelivery.merchant_id == merchant_id)
    status = _text(request.args.get('payment_status'))
    if status:
        if status not in ('unpaid', 'paid'):
            raise ValueError('payment_status must be unpaid or paid')
        query = query.filter(BDelivery.payment_status == status)
    date_from = request.args.get('date_from')
    if date_from:
        query = query.filter(BDelivery.invoice_date >= _parse_date(date_from, 'date_from'))
    date_to = request.args.get('date_to')
    if date_to:
        query = query.filter(BDelivery.invoice_date <= _parse_date(date_to, 'date_to'))
    rows = query.order_by(BDelivery.invoice_date.desc(), BDelivery.id.desc()).all()
    grand = round_money(0)
    unpaid = round_money(0)
    paid = round_money(0)
    for row in rows:
        total = round_money(row.grand_total)
        grand += total
        if row.payment_status == 'paid':
            paid += total
        else:
            unpaid += total
    return rows, {
        'count': len(rows),
        'grand_total': float(grand),
        'unpaid_total': float(unpaid),
        'paid_total': float(paid),
    }


@b_merchants_bp.route('/b-merchants', methods=['GET'])
def list_b_merchants():
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    merchants = BMerchant.query.order_by(BMerchant.name.asc()).all()
    return jsonify({'merchants': [merchant.to_dict() for merchant in merchants]}), 200


@b_merchants_bp.route('/b-merchants', methods=['POST'])
def create_b_merchant():
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    data = request.get_json(silent=True) or {}
    merchant = BMerchant(payment_terms=DEFAULT_PAYMENT_TERMS)
    try:
        _apply_merchant(merchant, data, partial=False)
        db.session.add(merchant)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f'Error creating B merchant: {exc}', exc_info=True)
        return jsonify({'error': 'Failed to create merchant'}), 500
    return jsonify({'merchant': merchant.to_dict()}), 201


@b_merchants_bp.route('/b-merchants/<int:merchant_id>', methods=['PUT'])
def update_b_merchant(merchant_id):
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    merchant = BMerchant.query.get_or_404(merchant_id)
    data = request.get_json(silent=True) or {}
    try:
        _apply_merchant(merchant, data, partial=True)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f'Error updating B merchant: {exc}', exc_info=True)
        return jsonify({'error': 'Failed to update merchant'}), 500
    return jsonify({'merchant': merchant.to_dict()}), 200


@b_merchants_bp.route('/b-merchants/<int:merchant_id>', methods=['DELETE'])
def delete_b_merchant(merchant_id):
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    merchant = BMerchant.query.get_or_404(merchant_id)
    if BDelivery.query.filter_by(merchant_id=merchant.id).first():
        return jsonify({'error': '商家已有送货记录，无法删除'}), 400
    try:
        db.session.delete(merchant)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f'Error deleting B merchant: {exc}', exc_info=True)
        return jsonify({'error': 'Failed to delete merchant'}), 500
    return jsonify({'message': 'Merchant deleted'}), 200


@b_merchants_bp.route('/b-deliveries', methods=['GET'])
def list_b_deliveries():
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    try:
        rows, aggregates = _filtered_deliveries()
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    return jsonify({
        'deliveries': [row.to_dict() for row in rows],
        'aggregates': aggregates,
    }), 200


@b_merchants_bp.route('/b-deliveries/<int:delivery_id>', methods=['GET'])
def get_b_delivery(delivery_id):
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    delivery = _delivery_query().filter(BDelivery.id == delivery_id).first_or_404()
    return jsonify({'delivery': delivery.to_dict()}), 200


@b_merchants_bp.route('/b-deliveries', methods=['POST'])
def create_b_delivery():
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    data = request.get_json(silent=True) or {}
    delivery = BDelivery(
        invoice_date=date.today(),
        due_date=date.today(),
        payment_terms=DEFAULT_PAYMENT_TERMS,
    )
    db.session.add(delivery)
    try:
        with db.session.no_autoflush:
            _apply_delivery(delivery, data)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f'Error creating B delivery: {exc}', exc_info=True)
        return jsonify({'error': 'Failed to create delivery'}), 500
    return jsonify({'delivery': delivery.to_dict()}), 201


@b_merchants_bp.route('/b-deliveries/<int:delivery_id>', methods=['PUT'])
def update_b_delivery(delivery_id):
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    delivery = _delivery_query().filter(BDelivery.id == delivery_id).first_or_404()
    data = request.get_json(silent=True) or {}
    try:
        _apply_delivery(delivery, data)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f'Error updating B delivery: {exc}', exc_info=True)
        return jsonify({'error': 'Failed to update delivery'}), 500
    return jsonify({'delivery': delivery.to_dict()}), 200


@b_merchants_bp.route('/b-deliveries/<int:delivery_id>', methods=['DELETE'])
def delete_b_delivery(delivery_id):
    _, error_response, status_code = _auth()
    if error_response:
        return error_response, status_code
    delivery = BDelivery.query.get_or_404(delivery_id)
    try:
        db.session.delete(delivery)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.error(f'Error deleting B delivery: {exc}', exc_info=True)
        return jsonify({'error': 'Failed to delete delivery'}), 500
    return jsonify({'message': 'Delivery deleted'}), 200
