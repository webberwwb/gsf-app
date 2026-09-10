"""Delivery 须知 consent endpoint and user flag."""
from datetime import timedelta

from constants.delivery_consent import DELIVERY_CONSENT_VERSION
from constants.status_enums import UserStatus
from models import db
from models.base import utc_now
from models.user import AuthToken, User


def _user():
    user = User(phone='+19025550111', nickname='Consent', status=UserStatus.ACTIVE.value)
    db.session.add(user)
    db.session.flush()
    return user


def _token(user):
    tok = AuthToken(
        user_id=user.id,
        token=f'tok-consent-{user.id}',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(tok)
    db.session.flush()
    return tok.token


def test_user_has_delivery_consent_false_by_default(app, db_session):
    user = _user()
    data = user.to_dict()
    assert data['has_delivery_consent'] is False


def test_accept_delivery_consent(app, db_session):
    user = _user()
    client = app.test_client()
    res = client.post(
        '/api/auth/me/delivery-consent',
        headers={'Authorization': f'Bearer {_token(user)}'},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body['user']['has_delivery_consent'] is True
    db_session.refresh(user)
    assert user.delivery_consent_version == DELIVERY_CONSENT_VERSION
    assert user.delivery_consent_accepted_at is not None


def test_accept_delivery_consent_requires_auth(app):
    client = app.test_client()
    res = client.post('/api/auth/me/delivery-consent')
    assert res.status_code == 401


def test_stale_consent_version_is_not_current(app, db_session):
    user = _user()
    user.delivery_consent_version = '2020-01'
    user.delivery_consent_accepted_at = utc_now()
    db.session.flush()
    assert user.to_dict()['has_delivery_consent'] is False


def test_unbind_card_revokes_delivery_consent(app, db_session):
    user = _user()
    user.delivery_consent_version = DELIVERY_CONSENT_VERSION
    user.delivery_consent_accepted_at = utc_now()
    user.stripe_payment_method_id = 'pm_1'
    user.stripe_card_last4 = '4242'
    db.session.flush()
    client = app.test_client()
    res = client.delete(
        '/api/payments/card',
        headers={'Authorization': f'Bearer {_token(user)}'},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body['has_card'] is False
    assert body['user']['has_delivery_consent'] is False
    db.session.refresh(user)
    assert user.stripe_payment_method_id is None
    assert user.delivery_consent_version is None
