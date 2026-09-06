"""Stale test-mode Stripe IDs must be replaced after switching to live keys."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from utils.stripe_payments import (
    LIVE_CARD_SETUP_PMC,
    card_setup_method_params,
    ensure_stripe_customer,
    sync_saved_card,
)


def _user(**overrides):
    data = dict(
        id=71,
        stripe_customer_id='cus_test_old',
        stripe_payment_method_id='pm_old',
        stripe_card_brand='visa',
        stripe_card_last4='4242',
        nickname='Weibo',
        wechat=None,
        phone='+19025809630',
    )
    data.update(overrides)
    return SimpleNamespace(**data)


def test_ensure_stripe_customer_recreates_when_missing(app):
    user = _user()
    client = MagicMock()
    missing = Exception('No such customer: cus_test_old')
    missing.code = 'resource_missing'
    client.v1.customers.retrieve.side_effect = missing
    client.v1.customers.create.return_value = SimpleNamespace(id='cus_live_new')

    with patch('utils.stripe_payments.get_stripe_client', return_value=client):
        customer_id = ensure_stripe_customer(user)

    assert customer_id == 'cus_live_new'
    assert user.stripe_customer_id == 'cus_live_new'
    assert user.stripe_payment_method_id is None
    assert user.stripe_card_last4 is None
    client.v1.customers.create.assert_called_once()


def test_ensure_stripe_customer_recreates_deleted(app):
    user = _user()
    client = MagicMock()
    client.v1.customers.retrieve.return_value = SimpleNamespace(
        id='cus_test_old', deleted=True, email=None
    )
    client.v1.customers.create.return_value = SimpleNamespace(id='cus_live_new')

    with patch('utils.stripe_payments.get_stripe_client', return_value=client):
        assert ensure_stripe_customer(user) == 'cus_live_new'
    assert user.stripe_customer_id == 'cus_live_new'


def test_ensure_stripe_customer_reuses_existing(app):
    user = _user(stripe_customer_id='cus_live')
    client = MagicMock()
    client.v1.customers.retrieve.return_value = SimpleNamespace(
        id='cus_live', email='grainstoryfarm@gmail.com', deleted=False
    )

    with patch('utils.stripe_payments.get_stripe_client', return_value=client):
        assert ensure_stripe_customer(user) == 'cus_live'
    client.v1.customers.create.assert_not_called()


def test_sync_saved_card_clears_missing_payment_method(app):
    user = _user()
    client = MagicMock()
    missing = Exception('No such payment_method')
    missing.code = 'resource_missing'
    client.v1.payment_methods.retrieve.side_effect = missing

    with patch('utils.stripe_payments.get_stripe_client', return_value=client):
        card = sync_saved_card(user)

    assert card['has_card'] is False
    assert user.stripe_payment_method_id is None
    assert user.stripe_card_last4 is None


def test_card_setup_uses_live_pmc(app):
    app.config['STRIPE_SECRET_KEY'] = 'sk_live_test'
    app.config['STRIPE_SETUP_PAYMENT_METHOD_CONFIG'] = ''
    assert card_setup_method_params() == {
        'payment_method_configuration': LIVE_CARD_SETUP_PMC,
    }


def test_card_setup_excludes_wallets_in_test_mode(app):
    app.config['STRIPE_SECRET_KEY'] = 'sk_test_test'
    app.config['STRIPE_SETUP_PAYMENT_METHOD_CONFIG'] = ''
    params = card_setup_method_params()
    assert 'klarna' in params['excluded_payment_method_types']
    assert 'pix' in params['excluded_payment_method_types']
    assert 'satispay' in params['excluded_payment_method_types']
