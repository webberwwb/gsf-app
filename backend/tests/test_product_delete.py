"""Deleting a product removes it from the catalog and leaves 下架 products listed."""
from datetime import datetime, timedelta

from models import db
from models.base import utc_now
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem
from models.product import Product
from models.user import AuthToken, User, UserRole
from constants.status_enums import UserStatus


def _user(phone, nickname):
    user = User(phone=phone, nickname=nickname, status=UserStatus.ACTIVE.value)
    db.session.add(user)
    db.session.flush()
    return user


def _admin():
    user = _user('+15550002001', 'Admin')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.flush()
    return user


def _headers(user):
    token = AuthToken(
        user_id=user.id,
        token=f'tok-product-delete-{user.id}',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(token)
    db.session.flush()
    return {'Authorization': f'Bearer {token.token}'}


def _product(name, **kwargs):
    product = Product(
        name=name,
        pricing_type='per_item',
        pricing_data={'price': 10},
        is_active=kwargs.pop('is_active', True),
        **kwargs,
    )
    db.session.add(product)
    db.session.flush()
    return product


def test_delete_removes_product_from_catalog_and_keeps_unlisted(app, db_session):
    admin = _admin()
    listed = _product('在售')
    unlisted = _product('下架', is_active=False)
    db.session.commit()
    client = app.test_client()
    headers = _headers(admin)

    deleted = client.delete(f'/api/admin/products/{listed.id}', headers=headers)
    assert deleted.status_code == 200, deleted.get_json()

    db.session.refresh(listed)
    assert listed.deleted_at is not None
    assert listed.is_active is True

    catalog = client.get('/api/admin/products', headers=headers)
    assert catalog.status_code == 200
    rows = {row['id']: row for row in catalog.get_json()['products']}
    assert listed.id not in rows
    assert rows[unlisted.id]['is_active'] is False

    public = client.get('/api/products')
    public_ids = [row['id'] for row in public.get_json()['products']]
    assert listed.id not in public_ids
    assert unlisted.id not in public_ids


def test_delete_drops_deal_link_and_keeps_order_line(app, db_session):
    admin = _admin()
    customer = _user('+15550002002', '顾客')
    product = _product('已下单')
    deal = GroupDeal(
        title='团',
        order_start_date=datetime(2026, 1, 1),
        order_end_date=datetime(2026, 12, 31),
        pickup_date=datetime(2026, 6, 1),
        status='active',
    )
    db.session.add(deal)
    db.session.flush()
    db.session.add(GroupDealProduct(group_deal_id=deal.id, product_id=product.id))
    order = Order(
        user_id=customer.id,
        group_deal_id=deal.id,
        order_number='DEL-1',
        subtotal=10,
        total=10,
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=10,
        total_price=10,
    ))
    db.session.commit()
    client = app.test_client()
    headers = _headers(admin)

    deleted = client.delete(f'/api/admin/products/{product.id}', headers=headers)
    assert deleted.status_code == 200, deleted.get_json()

    assert GroupDealProduct.query.filter_by(product_id=product.id).count() == 0
    assert OrderItem.query.filter_by(product_id=product.id).count() == 1
    assert db.session.get(Product, product.id) is not None

    catalog = client.get('/api/admin/products', headers=headers)
    ids = [row['id'] for row in catalog.get_json()['products']]
    assert product.id not in ids
