"""Stripe setup, off-session charge, and pay-again Checkout Session."""

import secrets
from decimal import Decimal

from flask import current_app
from utils.order_totals import calculate_amount_due
from utils.stripe_client import get_stripe_client, stripe_configured, stripe_secret_key


def _cents(amount):
    return int((Decimal(str(amount)) * 100).quantize(Decimal('1')))


STRIPE_CUSTOMER_EMAIL = 'grainstoryfarm@gmail.com'
CHECKOUT_DISPLAY_NAME = '谷语农庄APP'
# Live DIGITELF IT payment method config: cards only. Not a secret.
LIVE_CARD_SETUP_PMC = 'pmc_1UChD34icC7bDuRCzFtLf1Wz'
CARD_SETUP_EXCLUDED_TYPES = (
    'affirm',
    'afterpay_clearpay',
    'alipay',
    'bancontact',
    'blik',
    'eps',
    'ideal',
    'klarna',
    'mb_way',
    'p24',
    'paypal',
    'pix',
    'satispay',
    'sepa_debit',
    'sofort',
    'wechat_pay',
)


def card_setup_method_params():
    """Restrict bind-card to cards so Payment Element skips Satispay/Pix/Klarna."""
    pmc = (current_app.config.get('STRIPE_SETUP_PAYMENT_METHOD_CONFIG') or '').strip()
    if not pmc:
        key = stripe_secret_key()
        if key.startswith('sk_live_') or key.startswith('rk_live_'):
            pmc = LIVE_CARD_SETUP_PMC
    if pmc:
        return {'payment_method_configuration': pmc}
    return {'excluded_payment_method_types': list(CARD_SETUP_EXCLUDED_TYPES)}


def _is_missing_stripe_object(exc):
    code = getattr(exc, 'code', None)
    if code == 'resource_missing':
        return True
    return 'no such' in str(exc).lower()


def _clear_saved_card(user):
    user.stripe_payment_method_id = None
    user.stripe_card_brand = None
    user.stripe_card_last4 = None


def ensure_stripe_customer(user):
    client = get_stripe_client()
    if client is None:
        raise RuntimeError('Stripe is not configured')
    if user.stripe_customer_id:
        try:
            customer = client.v1.customers.retrieve(user.stripe_customer_id)
            if getattr(customer, 'deleted', False):
                raise RuntimeError('Stripe customer deleted')
            if getattr(customer, 'email', None) != STRIPE_CUSTOMER_EMAIL:
                try:
                    client.v1.customers.update(
                        user.stripe_customer_id,
                        params={'email': STRIPE_CUSTOMER_EMAIL},
                    )
                except Exception:
                    current_app.logger.warning('Could not set Stripe customer email', exc_info=True)
            return user.stripe_customer_id
        except Exception as exc:
            current_app.logger.warning(
                'Stale Stripe customer %s for user %s; creating a new one',
                user.stripe_customer_id,
                user.id,
                exc_info=_is_missing_stripe_object(exc) is False,
            )
            user.stripe_customer_id = None
            _clear_saved_card(user)

    params = {
        'metadata': {'user_id': str(user.id)},
        'name': user.nickname or user.wechat or user.phone or f'user-{user.id}',
        'email': STRIPE_CUSTOMER_EMAIL,
    }
    if user.phone:
        params['phone'] = user.phone
    customer = client.v1.customers.create(params=params)
    user.stripe_customer_id = customer.id
    return customer.id


def sync_saved_card(user):
    """Drop card-on-file fields that do not exist in the current Stripe mode."""
    if not user or not user.stripe_payment_method_id:
        return card_on_file_dict(user)
    client = get_stripe_client()
    if client is None:
        return card_on_file_dict(user)
    try:
        client.v1.payment_methods.retrieve(user.stripe_payment_method_id)
    except Exception as exc:
        if _is_missing_stripe_object(exc):
            current_app.logger.info(
                'Clearing stale payment method %s for user %s',
                user.stripe_payment_method_id,
                user.id,
            )
            _clear_saved_card(user)
        else:
            current_app.logger.warning('Could not verify saved payment method', exc_info=True)
    return card_on_file_dict(user)


def _create_with_optional_integration_id(create_fn, params):
    optional_keys = ('integration_identifier', 'branding_settings')
    try:
        return create_fn(params=params)
    except Exception as exc:
        message = str(exc)
        drop = [key for key in optional_keys if key in params and key in message]
        if not drop:
            raise
        fallback = {k: v for k, v in params.items() if k not in drop}
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


def create_setup_checkout_session(user, success_url, cancel_url):
    if not stripe_configured():
        raise RuntimeError('Stripe is not configured')
    client = get_stripe_client()
    customer_id = ensure_stripe_customer(user)
    suffix = secrets.token_hex(4)
    session = _create_with_optional_integration_id(client.v1.checkout.sessions.create, {
        'mode': 'setup',
        'currency': 'cad',
        'customer': customer_id,
        'success_url': success_url,
        'cancel_url': cancel_url,
        'metadata': {'user_id': str(user.id)},
        'branding_settings': {'display_name': CHECKOUT_DISPLAY_NAME},
        'custom_text': {
            'submit': {
                'message': '下单不扣款。称重和运费确定后，将从这张卡一次性扣款。',
            },
        },
        'integration_identifier': f'gsf_setup_{suffix}',
        **card_setup_method_params(),
    })
    return session


def create_setup_intent(user):
    if not stripe_configured():
        raise RuntimeError('Stripe is not configured')
    client = get_stripe_client()
    customer_id = ensure_stripe_customer(user)
    intent = client.v1.setup_intents.create(params={
        'customer': customer_id,
        'usage': 'off_session',
        'automatic_payment_methods': {'enabled': True},
        'metadata': {'user_id': str(user.id)},
        **card_setup_method_params(),
    })
    return intent


def complete_setup_intent(user, setup_intent_id):
    if not setup_intent_id:
        raise ValueError('缺少绑卡信息')
    client = get_stripe_client()
    intent = client.v1.setup_intents.retrieve(setup_intent_id)
    if getattr(intent, 'status', None) != 'succeeded':
        raise ValueError('绑卡未完成')
    customer_id = getattr(intent, 'customer', None)
    if customer_id and user.stripe_customer_id and customer_id != user.stripe_customer_id:
        raise ValueError('绑卡信息不匹配')
    pm_id = intent.payment_method
    if hasattr(pm_id, 'id'):
        pm_id = pm_id.id
    if not pm_id:
        raise ValueError('未找到银行卡')
    return apply_payment_method_to_user(user, pm_id, setup_intent_id=intent.id)


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
        'branding_settings': {'display_name': CHECKOUT_DISPLAY_NAME},
    }
    if order.stripe_customer_id:
        params['customer'] = order.stripe_customer_id
    session = _create_with_optional_integration_id(client.v1.checkout.sessions.create, params)
    order.stripe_payment_link_url = session.url
    return session
