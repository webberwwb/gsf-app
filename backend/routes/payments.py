"""Stripe setup, charge, pay-again link, and webhooks."""

from decimal import Decimal

from flask import Blueprint, jsonify, request, current_app
from models import db
from models.order import Order
from models.user import User, AuthToken
from constants.status_enums import PaymentStatus, PaymentMethod, DeliveryMethod
from utils.order_payment import mark_order_paid, copy_user_card_to_order
from utils.order_totals import calculate_amount_due
from utils.stripe_client import (
    stripe_configured,
    stripe_webhook_secret,
)
from utils.stripe_payments import (
    card_on_file_dict,
    create_setup_checkout_session,
    sync_setup_session,
    apply_payment_method_to_user,
    charge_order_off_session,
    create_pay_again_session,
)

payments_bp = Blueprint('payments', __name__)


def _require_user():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '').strip()
    else:
        token = auth_header.strip()
    if not token:
        return None, (jsonify({'error': 'No token provided'}), 401)
    auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
    if not auth_token or not auth_token.is_valid():
        return None, (jsonify({'error': 'Invalid or expired token'}), 401)
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None, (jsonify({'error': 'User not found or inactive'}), 401)
    return user, None


def _frontend_base():
    return (current_app.config.get('APP_FRONTEND_URL') or 'https://app.grainstoryfarm.ca').rstrip('/')


@payments_bp.route('/payments/config', methods=['GET'])
def payment_config():
    return jsonify({
        'configured': stripe_configured(),
        'publishable_key': (current_app.config.get('STRIPE_PUBLISHABLE_KEY') or ''),
    }), 200


@payments_bp.route('/payments/card', methods=['GET'])
def get_card_on_file():
    user, err = _require_user()
    if err:
        return err
    return jsonify(card_on_file_dict(user)), 200


@payments_bp.route('/payments/setup-session', methods=['POST'])
def create_setup_session():
    user, err = _require_user()
    if err:
        return err
    if not stripe_configured():
        return jsonify({'error': '在线支付尚未配置'}), 503
    body = request.get_json(silent=True) or {}
    email = (body.get('email') or '').strip() or None
    return_path = (body.get('return_path') or '/checkout').strip() or '/checkout'
    if not return_path.startswith('/'):
        return_path = '/checkout'
    base = _frontend_base()
    success_url = f'{base}{return_path}?card_setup=success&session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{base}{return_path}?card_setup=cancel'
    try:
        session = create_setup_checkout_session(user, success_url, cancel_url, email=email)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Stripe setup session failed: %s', e, exc_info=True)
        return jsonify({'error': '无法创建绑卡页面', 'message': str(e)}), 502
    return jsonify({'url': session.url, 'session_id': session.id}), 200


@payments_bp.route('/payments/setup-session/<session_id>', methods=['GET'])
def complete_setup_session(session_id):
    user, err = _require_user()
    if err:
        return err
    if not stripe_configured():
        return jsonify({'error': '在线支付尚未配置'}), 503
    try:
        card = sync_setup_session(user, session_id)
        if not card:
            return jsonify({'error': '尚未完成绑卡', 'has_card': False}), 400
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Sync setup session failed: %s', e, exc_info=True)
        return jsonify({'error': '同步绑卡失败', 'message': str(e)}), 502
    return jsonify({**card_on_file_dict(user), **card}), 200


@payments_bp.route('/payments/webhook', methods=['POST'])
def stripe_webhook():
    secret = stripe_webhook_secret()
    if not secret:
        return jsonify({'error': 'Webhook secret not configured'}), 503
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature', '')
    try:
        import stripe
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except Exception as e:
        current_app.logger.warning('Stripe webhook signature failed: %s', e)
        return jsonify({'error': 'Invalid signature'}), 400

    event_type = event.get('type') if isinstance(event, dict) else event.type
    data = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
    if hasattr(data, 'to_dict'):
        data = data.to_dict()

    try:
        if event_type == 'checkout.session.completed':
            _handle_checkout_completed(data)
        elif event_type == 'setup_intent.succeeded':
            _handle_setup_intent_succeeded(data)
        elif event_type == 'payment_intent.succeeded':
            _handle_payment_intent_succeeded(data)
        elif event_type == 'payment_intent.payment_failed':
            _handle_payment_intent_failed(data)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Stripe webhook handler failed: %s', e, exc_info=True)
        return jsonify({'error': 'handler failed'}), 500

    return jsonify({'received': True}), 200


def _handle_checkout_completed(session):
    mode = session.get('mode')
    metadata = session.get('metadata') or {}
    if mode == 'setup':
        user_id = metadata.get('user_id')
        user = User.query.get(int(user_id)) if user_id else None
        if not user:
            return
        setup_intent = session.get('setup_intent')
        if isinstance(setup_intent, dict):
            pm_id = setup_intent.get('payment_method')
            if isinstance(pm_id, dict):
                pm_id = pm_id.get('id')
        else:
            sync_setup_session(user, session.get('id'))
            return
        if pm_id:
            apply_payment_method_to_user(user, pm_id)
        return

    if mode == 'payment':
        order = _order_from_stripe_metadata(metadata)
        if not order or order.payment_status == PaymentStatus.PAID.value:
            return
        pi = session.get('payment_intent')
        pi_id = pi.get('id') if isinstance(pi, dict) else pi
        amount_total = session.get('amount_total')
        charged = Decimal(str(amount_total)) / 100 if amount_total is not None else None
        order.stripe_charge_status = 'succeeded'
        order.stripe_last_error = None
        mark_order_paid(order, transaction_id=pi_id, amount_charged=charged)


def _handle_setup_intent_succeeded(setup_intent):
    metadata = setup_intent.get('metadata') or {}
    user_id = metadata.get('user_id')
    user = User.query.get(int(user_id)) if user_id else None
    pm_id = setup_intent.get('payment_method')
    if isinstance(pm_id, dict):
        pm_id = pm_id.get('id')
    if user and pm_id:
        apply_payment_method_to_user(user, pm_id, setup_intent_id=setup_intent.get('id'))


def _handle_payment_intent_succeeded(pi):
    order = _order_from_payment_intent(pi)
    if not order or order.payment_status == PaymentStatus.PAID.value:
        return
    amount = pi.get('amount_received') or pi.get('amount')
    charged = Decimal(str(amount)) / 100 if amount is not None else None
    order.stripe_charge_status = 'succeeded'
    order.stripe_last_error = None
    mark_order_paid(order, transaction_id=pi.get('id'), amount_charged=charged)


def _handle_payment_intent_failed(pi):
    order = _order_from_payment_intent(pi)
    if not order or order.payment_status == PaymentStatus.PAID.value:
        return
    last_err = pi.get('last_payment_error') or {}
    order.stripe_charge_status = 'failed'
    order.stripe_last_error = last_err.get('message') or '扣款失败'
    if pi.get('id'):
        order.payment_transaction_id = pi.get('id')


def _order_from_stripe_metadata(metadata):
    order_id = (metadata or {}).get('order_id')
    if not order_id:
        return None
    return Order.query.filter(Order.id == int(order_id), Order.deleted_at.is_(None)).first()


def _order_from_payment_intent(pi):
    order = _order_from_stripe_metadata(pi.get('metadata') or {})
    if order:
        return order
    pi_id = pi.get('id')
    if not pi_id:
        return None
    return Order.query.filter(
        Order.payment_transaction_id == pi_id,
        Order.deleted_at.is_(None),
    ).first()


def _require_admin():
    from routes.admin import require_admin_auth
    return require_admin_auth()


@payments_bp.route('/admin/orders/<int:order_id>/stripe-charge', methods=['POST'])
def admin_stripe_charge(order_id):
    user_id, error_response, status_code = _require_admin()
    if error_response:
        return error_response, status_code
    if not stripe_configured():
        return jsonify({'error': '在线支付尚未配置'}), 503
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order.payment_status == PaymentStatus.PAID.value:
        return jsonify({'error': '订单已付款', 'order': _order_payload(order)}), 400
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        return jsonify({'error': '仅配送订单可在线扣款'}), 400
    if not order.stripe_payment_method_id:
        user = User.query.get(order.user_id)
        copy_user_card_to_order(order, user)
    ok, pi, err = charge_order_off_session(order)
    pi_id = getattr(pi, 'id', None) if pi is not None else None
    if ok:
        amount = calculate_amount_due(order)
        order.stripe_charge_status = 'succeeded'
        order.stripe_last_error = None
        mark_order_paid(order, transaction_id=pi_id, amount_charged=amount)
        db.session.commit()
        return jsonify({'message': '扣款成功', 'order': _order_payload(order)}), 200

    order.stripe_charge_status = 'failed'
    order.stripe_last_error = err
    if pi_id:
        order.payment_transaction_id = pi_id
    try:
        create_pay_again_session(
            order,
            success_url=f'{_frontend_base()}/orders/{order.id}?paid=1',
            cancel_url=f'{_frontend_base()}/orders/{order.id}?paid=0',
        )
    except Exception as e:
        current_app.logger.error('Pay-again session failed: %s', e, exc_info=True)
    db.session.commit()
    return jsonify({
        'error': err or '扣款失败',
        'order': _order_payload(order),
    }), 402


@payments_bp.route('/admin/orders/<int:order_id>/stripe-payment-link', methods=['POST'])
def admin_stripe_payment_link(order_id):
    user_id, error_response, status_code = _require_admin()
    if error_response:
        return error_response, status_code
    if not stripe_configured():
        return jsonify({'error': '在线支付尚未配置'}), 503
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order.payment_status == PaymentStatus.PAID.value:
        return jsonify({'error': '订单已付款'}), 400
    try:
        create_pay_again_session(
            order,
            success_url=f'{_frontend_base()}/orders/{order.id}?paid=1',
            cancel_url=f'{_frontend_base()}/orders/{order.id}?paid=0',
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '无法创建付款链接', 'message': str(e)}), 502
    return jsonify({'url': order.stripe_payment_link_url, 'order': _order_payload(order)}), 200


def _order_payload(order):
    data = order.to_dict()
    user = User.query.get(order.user_id)
    if user:
        data['user'] = {
            'id': user.id,
            'nickname': user.nickname,
            'phone': user.phone,
            'email': user.email,
            'wechat': user.wechat,
            'is_admin': user.is_admin,
        }
    return data
