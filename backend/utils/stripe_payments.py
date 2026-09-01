"""Stripe setup, off-session charge, and pay-again Checkout Session."""

import secrets
from decimal import Decimal

from flask import current_app
from models.user import User
from utils.order_totals import calculate_amount_due
from utils.stripe_client import get_stripe_client, stripe_configured


def _cents(amount):
    return int((Decimal(str(amount)) * 100).quantize(Decimal('1')))


def ensure_stripe_customer(user, email=None):
    client = get_stripe_client()
    if client is None:
        raise RuntimeError('Stripe is not configured')
    if email:
        _maybe_set_user_email(user, email)
    if user.stripe_customer_id:
        if email:
            try:
                client.v1.customers.update(
                    user.stripe_customer_id,
                    params={'email': email},
                )
            except Exception:
                current_app.logger.warning('Could not update Stripe customer email', exc_info=True)
        return user.stripe_customer_id

    params = {
        'metadata': {'user_id': str(user.id)},
        'name': user.nickname or user.wechat or user.phone or f'user-{user.id}',
    }
    if user.phone:
        params['phone'] = user.phone
    if user.email:
        params['email'] = user.email
    customer = client.v1.customers.create(params=params)
    user.stripe_customer_id = customer.id
    return customer.id


def _maybe_set_user_email(user, email):
    email = (email or '').strip()
    if not email:
        return
    if user.email == email:
        return
    taken = User.query.filter(User.email == email, User.id != user.id).first()
    if taken:
        raise ValueError('该邮箱已被其他账号使用')
    user.email = email


def _create_with_optional_integration_id(create_fn, params):
    try:
        return create_fn(params=params)
    except Exception as exc:
        if 'integration_identifier' not in params or 'integration_identifier' not in str(exc):
            raise
        fallback = {k: v for k, v in params.items() if k != 'integration_identifier'}
        return create_fn(params=fallback)


def apply_payment_method_to_user(user, payment_method_id, setup_intent_id=None):
    client = get_stripe_client()
    if user.stripe_customer_id:
        try:
            client.v1.payment_methods.attach(
                payment_method_id,
                params={'customer': user.stripe_customer_id},
            )
        except Exception:
            current_app.logger.info('Payment method already attached or attach skipped')
        try:
            client.v1.customers.update(
                user.stripe_customer_id,
                params={'invoice_settings': {'default_payment_method': payment_method_id}},
            )
        except Exception:
            current_app.logger.info('Could not set default payment method')
    pm = client.v1.payment_methods.retrieve(payment_method_id)
    card = getattr(pm, 'card', None)
    user.stripe_payment_method_id = payment_method_id
    user.stripe_card_brand = getattr(card, 'brand', None) if card else None
    user.stripe_card_last4 = getattr(card, 'last4', None) if card else None
    if setup_intent_id:
        pass
    return {
        'brand': user.stripe_card_brand,
        'last4': user.stripe_card_last4,
        'payment_method_id': payment_method_id,
    }


def create_setup_checkout_session(user, success_url, cancel_url, email=None):
    if not stripe_configured():
        raise RuntimeError('Stripe is not configured')
    client = get_stripe_client()
    customer_id = ensure_stripe_customer(user, email=email)
    suffix = secrets.token_hex(4)
    session = _create_with_optional_integration_id(client.v1.checkout.sessions.create, {
        'mode': 'setup',
        'currency': 'cad',
        'customer': customer_id,
        'success_url': success_url,
        'cancel_url': cancel_url,
        'metadata': {'user_id': str(user.id)},
        'custom_text': {
            'submit': {
                'message': '下单不扣款。称重和运费确定后，将从这张卡一次性扣款。',
            },
        },
        'integration_identifier': f'gsf_setup_{suffix}',
    })
    return session


def sync_setup_session(user, session_id):
    client = get_stripe_client()
    session = client.v1.checkout.sessions.retrieve(
        session_id,
        params={'expand': ['setup_intent']},
    )
    if getattr(session, 'status', None) not in ('complete', 'expired') and getattr(session, 'setup_intent', None) is None:
        return None
    setup_intent = session.setup_intent
    if setup_intent is None:
        return None
    if isinstance(setup_intent, str):
        setup_intent = client.v1.setup_intents.retrieve(setup_intent)
    pm_id = setup_intent.payment_method
    if isinstance(pm_id, dict) or hasattr(pm_id, 'id'):
        pm_id = getattr(pm_id, 'id', None) or (pm_id.get('id') if isinstance(pm_id, dict) else None)
    if not pm_id:
        return None
    return apply_payment_method_to_user(user, pm_id, setup_intent_id=setup_intent.id)


def card_on_file_dict(user):
    if not user or not user.stripe_payment_method_id:
        return {'has_card': False, 'brand': None, 'last4': None}
    return {
        'has_card': True,
        'brand': user.stripe_card_brand,
        'last4': user.stripe_card_last4,
        'payment_method_id': user.stripe_payment_method_id,
    }


def charge_order_off_session(order):
    """Charge amount_due. Returns (ok, payment_intent_or_none, error_message)."""
    if not stripe_configured():
        return False, None, 'Stripe is not configured'
    client = get_stripe_client()
    amount = calculate_amount_due(order)
    cents = _cents(amount)
    if cents <= 0:
        return False, None, '应付金额为 0，无需扣款'
    if not order.stripe_customer_id or not order.stripe_payment_method_id:
        return False, None, '订单未绑定银行卡'
    suffix = secrets.token_hex(4)
    try:
        pi = _create_with_optional_integration_id(client.v1.payment_intents.create, {
            'amount': cents,
            'currency': 'cad',
            'customer': order.stripe_customer_id,
            'payment_method': order.stripe_payment_method_id,
            'off_session': True,
            'confirm': True,
            'metadata': {
                'order_id': str(order.id),
                'order_number': order.order_number or '',
            },
            'description': f'谷语农庄 {order.order_number}',
            'integration_identifier': f'gsf_charge_{suffix}',
        })
    except Exception as exc:
        err = getattr(exc, 'user_message', None) or str(exc)
        pi = getattr(exc, 'error', None)
        pi_obj = None
        if hasattr(exc, 'error') and getattr(exc.error, 'payment_intent', None):
            pi_obj = exc.error.payment_intent
        return False, pi_obj, err

    status = getattr(pi, 'status', None)
    if status == 'succeeded':
        return True, pi, None
    return False, pi, f'扣款未完成（{status}）'


def create_pay_again_session(order, success_url, cancel_url):
    client = get_stripe_client()
    amount = calculate_amount_due(order)
    cents = _cents(amount)
    if cents <= 0:
        raise ValueError('应付金额为 0')
    suffix = secrets.token_hex(4)
    params = {
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'line_items': [{
            'price_data': {
                'currency': 'cad',
                'unit_amount': cents,
                'product_data': {'name': f'订单 {order.order_number}'},
            },
            'quantity': 1,
        }],
        'metadata': {
            'order_id': str(order.id),
            'order_number': order.order_number or '',
        },
        'integration_identifier': f'gsf_paylink_{suffix}',
    }
    if order.stripe_customer_id:
        params['customer'] = order.stripe_customer_id
    session = _create_with_optional_integration_id(client.v1.checkout.sessions.create, params)
    order.stripe_payment_link_url = session.url
    return session
