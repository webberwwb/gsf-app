"""Admin can create an order for an existing customer after the deal is closed."""
from datetime import datetime, timedelta

from constants.status_enums import OrderStatus, UserStatus
from models import db
from models.address import Address
from models.base import utc_now
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order
from models.product import Product
from models.user import AuthToken, User, UserRole
from utils.stock_management import get_available_stock


def _user(phone, nickname, **kwargs):
    user = User(phone=phone, nickname=nickname, status=UserStatus.ACTIVE.value, **kwargs)
    db.session.add(user)
    db.session.flush()
    return user


def _admin():
    user = _user('+15550001001', 'Admin')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.flush()
    return user


def _headers(user):
    existing = AuthToken.query.filter_by(user_id=user.id, is_revoked=False).first()
    if existing:
        return {'Authorization': f'Bearer {existing.token}'}
    token = AuthToken(
        user_id=user.id,
        token=f'tok-admin-create-{user.id}',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(token)
    db.session.flush()
    return {'Authorization': f'Bearer {token.token}'}


def _deal(**kwargs):
    data = dict(
        title='团',
        order_start_date=datetime(2026, 1, 1),
        order_end_date=datetime(2026, 12, 31),
        pickup_date=datetime(2026, 6, 1),
        status='active',
    )
    data.update(kwargs)
    deal = GroupDeal(**data)
    db.session.add(deal)
    db.session.flush()
    return deal


def _product():
    product = Product(
        name='菜',
        pricing_type='per_item',
        pricing_data={'price': 10},
        is_active=True,
    )
    db.session.add(product)
    db.session.flush()
    return product


def _link(deal, product, stock=None):
    row = GroupDealProduct(
        group_deal_id=deal.id,
        product_id=product.id,
        deal_stock_limit=stock,
    )
    db.session.add(row)
    db.session.flush()
    return row


def _closed_deal():
    return _deal(
        status='closed',
        order_start_date=datetime(2020, 1, 1),
        order_end_date=datetime(2020, 1, 2),
        pickup_date=datetime(2020, 1, 3),
    )


def test_customer_cannot_order_after_cutoff_but_admin_can(app, db_session):
    customer = _user('+15550001002', '顾客')
    admin = _admin()
    deal = _closed_deal()
    product = _product()
    _link(deal, product, stock=5)
    client = app.test_client()
    payload = {
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 2}],
    }

    blocked = client.post('/api/orders', headers=_headers(customer), json=payload)
    assert blocked.status_code == 400

    created = client.post('/api/admin/orders', headers=_headers(admin), json={
        **payload,
        'user_id': customer.id,
        'notes': '截单后补单',
    })
    assert created.status_code == 201, created.get_json()
    body = created.get_json()['order']
    assert body['user_id'] == customer.id
    assert body['group_deal_id'] == deal.id
    assert body['status'] == OrderStatus.CONFIRMED.value
    assert body['notes'] == '截单后补单'
    assert body['items'][0]['quantity'] == 2
    assert get_available_stock(deal.id, product.id) == 3

    again = client.post('/api/admin/orders', headers=_headers(admin), json={
        **payload,
        'user_id': customer.id,
    })
    assert again.status_code == 201, again.get_json()
    assert Order.query.filter_by(user_id=customer.id, group_deal_id=deal.id).count() == 2


def test_admin_create_uses_submitted_while_deal_is_open(app, db_session):
    customer = _user('+15550001003', '顾客')
    admin = _admin()
    deal = _deal()
    product = _product()
    _link(deal, product, stock=2)
    client = app.test_client()

    created = client.post('/api/admin/orders', headers=_headers(admin), json={
        'user_id': customer.id,
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    assert created.get_json()['order']['status'] == OrderStatus.SUBMITTED.value


def test_admin_create_follows_preparing_deal(app, db_session):
    customer = _user('+15550001004', '顾客')
    admin = _admin()
    deal = _deal(status='preparing', order_end_date=datetime(2020, 1, 2))
    product = _product()
    _link(deal, product)
    client = app.test_client()

    created = client.post('/api/admin/orders', headers=_headers(admin), json={
        'user_id': customer.id,
        'group_deal_id': deal.id,
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    assert created.get_json()['order']['status'] == OrderStatus.PREPARING.value
    assert created.get_json()['order']['pickup_location'] == 'markham'


def test_admin_create_rejects_insufficient_stock_and_non_admin(app, db_session):
    customer = _user('+15550001005', '顾客')
    admin = _admin()
    deal = _closed_deal()
    product = _product()
    _link(deal, product, stock=0)
    client = app.test_client()
    payload = {
        'user_id': customer.id,
        'group_deal_id': deal.id,
        'items': [{'product_id': product.id, 'quantity': 1}],
    }

    denied = client.post('/api/admin/orders', headers=_headers(customer), json=payload)
    assert denied.status_code == 403

    blocked = client.post('/api/admin/orders', headers=_headers(admin), json=payload)
    assert blocked.status_code == 400
    assert '库存' in blocked.get_json()['error']


def test_admin_delivery_order_requires_customer_address(app, db_session):
    customer = _user('+15550001006', '顾客')
    admin = _admin()
    deal = _closed_deal()
    product = _product()
    _link(deal, product, stock=3)
    address = Address(
        user_id=customer.id,
        recipient_name='顾客',
        phone=customer.phone,
        address_line1='1 Main',
        city='Markham',
        postal_code='L3R 0A1',
    )
    db.session.add(address)
    db.session.flush()
    client = app.test_client()

    missing = client.post('/api/admin/orders', headers=_headers(admin), json={
        'user_id': customer.id,
        'group_deal_id': deal.id,
        'delivery_method': 'delivery',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert missing.status_code == 400

    created = client.post('/api/admin/orders', headers=_headers(admin), json={
        'user_id': customer.id,
        'group_deal_id': deal.id,
        'delivery_method': 'delivery',
        'address_id': address.id,
        'payment_method': 'etransfer',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    assert order['delivery_method'] == 'delivery'
    assert order['address_id'] == address.id
    assert order['payment_method'] == 'etransfer'
