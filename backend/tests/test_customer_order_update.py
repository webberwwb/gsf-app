"""Customer PATCH is settings-vs-items; stock uses summed qty; admin add also reserves."""
from datetime import datetime, timedelta
from decimal import Decimal

from constants.status_enums import OrderStatus, UserStatus
from models import db
from models.base import utc_now
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order
from models.product import Product
from models.user import AuthToken, User, UserRole
from utils.stock_management import (
    get_available_stock,
    qty_by_product,
    update_stock_after_order_modification,
)


def _user(phone, nickname, **kwargs):
    u = User(phone=phone, nickname=nickname, status=UserStatus.ACTIVE.value, **kwargs)
    db.session.add(u)
    db.session.flush()
    return u


def _admin():
    user = _user('+15551111999', 'Admin')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.flush()
    return user


def _token(user):
    existing = AuthToken.query.filter_by(user_id=user.id, is_revoked=False).first()
    if existing:
        return existing.token
    tok = AuthToken(
        user_id=user.id,
        token=f'tok-upd-{user.id}-{user.phone}',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(tok)
    db.session.flush()
    return tok.token


def _headers(user):
    return {'Authorization': f'Bearer {_token(user)}'}


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


def _product(name='菜', price=10, **kwargs):
    pricing_type = kwargs.pop('pricing_type', 'per_item')
    pricing_data = kwargs.pop('pricing_data', {'price': price})
    p = Product(
        name=name,
        pricing_type=pricing_type,
        pricing_data=pricing_data,
        is_active=True,
        **kwargs,
    )
    db.session.add(p)
    db.session.flush()
    return p


def _link(deal, product, stock=None):
    row = GroupDealProduct(
        group_deal_id=deal.id,
        product_id=product.id,
        deal_stock_limit=stock,
    )
    db.session.add(row)
    db.session.flush()
    return row


def _stock(deal, product):
    db.session.expire_all()
    return get_available_stock(deal.id, product.id)


def _cap(deal, product):
    db.session.expire_all()
    return GroupDealProduct.query.filter_by(
        group_deal_id=deal.id, product_id=product.id
    ).first().deal_stock_limit


def test_qty_by_product_sums_duplicate_lines():
    assert qty_by_product([
        {'product_id': 5, 'quantity': 1},
        {'product_id': 5, 'quantity': 1},
        {'product_id': 5, 'quantity': 1},
    ])[5] == 3
    assert qty_by_product([
        {'product_id': 5, 'quantity': 3},
    ])[5] == 3


def test_stock_helper_weight_shape_is_net_zero(app, db_session):
    deal = _deal()
    product = _product()
    _link(deal, product, stock=0)
    ok, err = update_stock_after_order_modification(
        deal.id,
        [
            {'product_id': product.id, 'quantity': 1},
            {'product_id': product.id, 'quantity': 1},
            {'product_id': product.id, 'quantity': 1},
        ],
        [{'product_id': product.id, 'quantity': 3}],
    )
    assert ok is True
    assert err is None
    assert _stock(deal, product) == 0


def test_notes_only_keeps_limited_stock_and_item_ids(app, db_session):
    user = _user('+15551111001', '买家')
    deal = _deal()
    product = _product()
    _link(deal, product, stock=1)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    item_id = order['items'][0]['id']
    assert _stock(deal, product) == 0

    patched = client.patch(f"/api/orders/{order['id']}", headers=_headers(user), json={
        'notes': '少盐',
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'pickup_location': 'markham',
    })
    assert patched.status_code == 200, patched.get_json()
    body = patched.get_json()['order']
    assert body['notes'] == '少盐'
    assert [i['id'] for i in body['items']] == [item_id]
    assert _stock(deal, product) == 0


def test_weight_notes_only_keeps_ids(app, db_session):
    user = _user('+15551111002', '买家')
    deal = _deal()
    product = _product(
        '肉',
        pricing_type='bundled_weight',
        pricing_data={'price_per_unit': 5, 'min_weight': 7, 'max_weight': 15},
    )
    _link(deal, product, stock=3)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 3, 'pricing_type': 'bundled_weight'}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    ids = [i['id'] for i in order['items']]
    assert len(ids) == 3
    assert _stock(deal, product) == 0

    patched = client.patch(f"/api/orders/{order['id']}", headers=_headers(user), json={
        'notes': '切块',
        'delivery_method': 'pickup',
        'payment_method': 'cash',
    })
    assert patched.status_code == 200, patched.get_json()
    assert [i['id'] for i in patched.get_json()['order']['items']] == ids
    assert _stock(deal, product) == 0


def test_increase_qty_deducts_one_and_keeps_existing_id(app, db_session):
    user = _user('+15551111003', '买家')
    deal = _deal()
    product = _product()
    _link(deal, product, stock=5)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 2}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    item_id = order['items'][0]['id']

    patched = client.patch(f"/api/orders/{order['id']}", headers=_headers(user), json={
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'id': item_id, 'product_id': product.id, 'quantity': 3}],
    })
    assert patched.status_code == 200, patched.get_json()
    items = patched.get_json()['order']['items']
    assert len(items) == 1
    assert items[0]['id'] == item_id
    assert items[0]['quantity'] == 3
    assert _stock(deal, product) == 2


def test_decrease_weight_qty_restores_stock_and_soft_deletes_extra(app, db_session):
    user = _user('+15551111004', '买家')
    deal = _deal()
    product = _product(
        '肉',
        pricing_type='bundled_weight',
        pricing_data={'price_per_unit': 5, 'min_weight': 7, 'max_weight': 15},
    )
    _link(deal, product, stock=5)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 3, 'pricing_type': 'bundled_weight'}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    ids = [i['id'] for i in order['items']]

    patched = client.patch(f"/api/orders/{order['id']}", headers=_headers(user), json={
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 2, 'pricing_type': 'bundled_weight'}],
    })
    assert patched.status_code == 200, patched.get_json()
    new_ids = [i['id'] for i in patched.get_json()['order']['items']]
    assert len(new_ids) == 2
    assert set(new_ids).issubset(set(ids))
    assert _stock(deal, product) == 3


def test_confirmed_rejects_items_allows_notes(app, db_session):
    user = _user('+15551111005', '买家')
    deal = _deal()
    product = _product()
    _link(deal, product, stock=2)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    order_id = created.get_json()['order']['id']
    item_id = created.get_json()['order']['items'][0]['id']
    row = Order.query.get(order_id)
    row.status = OrderStatus.CONFIRMED.value
    db.session.commit()

    blocked = client.patch(f'/api/orders/{order_id}', headers=_headers(user), json={
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'id': item_id, 'product_id': product.id, 'quantity': 2}],
    })
    assert blocked.status_code == 400
    assert '不可修改商品' in (blocked.get_json() or {}).get('error', '')

    notes = client.patch(f'/api/orders/{order_id}', headers=_headers(user), json={
        'notes': '门口放',
        'delivery_method': 'pickup',
        'payment_method': 'cash',
    })
    assert notes.status_code == 200, notes.get_json()
    assert notes.get_json()['order']['notes'] == '门口放'
    assert notes.get_json()['order']['can_edit_settings'] is True
    assert notes.get_json()['order']['can_edit_products'] is False


def test_packing_complete_rejects_notes(app, db_session):
    user = _user('+15551111006', '买家')
    deal = _deal()
    product = _product()
    _link(deal, product, stock=1)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    order_id = created.get_json()['order']['id']
    row = Order.query.get(order_id)
    row.status = OrderStatus.PACKING_COMPLETE.value
    db.session.commit()

    res = client.patch(f'/api/orders/{order_id}', headers=_headers(user), json={
        'notes': '改不了',
        'delivery_method': 'pickup',
        'payment_method': 'cash',
    })
    assert res.status_code == 400


def test_admin_add_respects_stock(app, db_session):
    customer = _user('+15551111007', '买家')
    admin = _admin()
    deal = _deal()
    product = _product()
    _link(deal, product, stock=1)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(customer), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    item = order['items'][0]
    assert _stock(deal, product) == 0

    blocked = client.put(f"/api/admin/orders/{order['id']}/update", headers=_headers(admin), json={
        'items': [
            {
                'id': item['id'],
                'product_id': product.id,
                'quantity': 2,
                'pricing_type': 'per_item',
            }
        ],
    })
    assert blocked.status_code == 400
    assert '库存不足' in (blocked.get_json() or {}).get('error', '')
    assert _stock(deal, product) == 0

    other = _product('蛋', price=8)
    _link(deal, other, stock=1)
    added = client.put(f"/api/admin/orders/{order['id']}/update", headers=_headers(admin), json={
        'items': [
            {
                'id': item['id'],
                'product_id': product.id,
                'quantity': 1,
                'pricing_type': 'per_item',
            },
            {'product_id': other.id, 'quantity': 1, 'pricing_type': 'per_item'},
        ],
    })
    assert added.status_code == 200, added.get_json()
    assert _stock(deal, product) == 0
    assert _stock(deal, other) == 0


def test_cancel_and_reactivate_return_edit_flags(app, db_session):
    user = _user('+15551111008', '买家')
    deal = _deal()
    product = _product()
    _link(deal, product, stock=2)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    order_id = created.get_json()['order']['id']

    cancelled = client.post(f'/api/orders/{order_id}/cancel', headers=_headers(user))
    assert cancelled.status_code == 200, cancelled.get_json()
    cancelled_order = cancelled.get_json()['order']
    assert cancelled_order['status'] == OrderStatus.CANCELLED.value
    assert cancelled_order['can_edit_settings'] is False
    assert cancelled_order['can_edit_products'] is False
    assert cancelled_order['is_editable'] is False
    assert cancelled_order['group_deal']['status'] == 'active'

    reactivated = client.post(f'/api/orders/{order_id}/reactivate', headers=_headers(user))
    assert reactivated.status_code == 200, reactivated.get_json()
    live = reactivated.get_json()['order']
    assert live['status'] == OrderStatus.SUBMITTED.value
    assert live['can_edit_settings'] is True
    assert live['can_edit_products'] is True
    assert live['is_editable'] is True
    assert live['group_deal']['status'] == 'active'


def test_deal_stock_limit_is_cap_not_remaining(app, db_session):
    user = _user('+15551111009', '买家')
    admin = _admin()
    deal = _deal()
    product = _product()
    _link(deal, product, stock=2)
    client = app.test_client()
    first = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert first.status_code == 201, first.get_json()
    assert _cap(deal, product) == 2
    assert _stock(deal, product) == 1

    saved = client.put(f'/api/admin/group-deals/{deal.id}', headers=_headers(admin), json={
        'title': deal.title,
        'order_start_date': deal.order_start_date.isoformat(),
        'order_end_date': deal.order_end_date.isoformat(),
        'pickup_date': deal.pickup_date.isoformat(),
        'status': deal.status,
        'products': [{'product_id': product.id, 'deal_stock_limit': 2}],
    })
    assert saved.status_code == 200, saved.get_json()
    admin_product = saved.get_json()['group_deal']['products'][0]
    assert admin_product['deal_stock_limit'] == 2
    assert admin_product['deal_stock_remaining'] == 1
    assert _cap(deal, product) == 2
    assert _stock(deal, product) == 1

    blocked = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 2}],
    })
    assert blocked.status_code == 400
    assert '库存不足' in (blocked.get_json() or {}).get('error', '')
    assert _cap(deal, product) == 2
    assert _stock(deal, product) == 1


def test_cutting_rejected_when_product_does_not_offer_it(app, db_session):
    user = _user('+15551111021', '买家')
    deal = _deal()
    product = _product()
    _link(deal, product, stock=5)
    client = app.test_client()
    res = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1, 'cutting': True}],
    })
    assert res.status_code == 400
    assert '不提供切分' in (res.get_json() or {}).get('error', '')


def test_cutting_fee_added_and_split_from_uncut_line(app, db_session):
    user = _user('+15551111022', '买家')
    deal = _deal()
    product = _product(price=10, cutting_enabled=True, cutting_fee=2)
    _link(deal, product, stock=5)
    client = app.test_client()
    res = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [
            {'product_id': product.id, 'quantity': 2, 'cutting': False},
            {'product_id': product.id, 'quantity': 1, 'cutting': True},
        ],
    })
    assert res.status_code == 201, res.get_json()
    items = res.get_json()['order']['items']
    assert len(items) == 2
    by_cut = {bool(i['cutting']): i for i in items}
    assert by_cut[False]['quantity'] == 2
    assert float(by_cut[False]['total_price']) == 20
    assert by_cut[True]['quantity'] == 1
    assert float(by_cut[True]['total_price']) == 12
    assert float(by_cut[True]['cutting_fee']) == 2
    assert '切分' in (by_cut[True].get('display_name') or '')


def test_admin_order_detail_includes_deal_sale_on_item_product(app, db_session):
    user = _user('+15551111888', '买家')
    admin = _admin()
    deal = _deal()
    product = _product(
        '鹧鸪',
        price=16.99,
        pricing_data={'price': 16.99, 'sale_price': 14.99},
    )
    link = _link(deal, product)
    link.is_discount = True
    db_session.flush()

    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'product_id': product.id, 'quantity': 1}],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    assert float(order['items'][0]['unit_price']) == 14.99

    detail = client.get(f"/api/admin/orders/{order['id']}", headers=_headers(admin))
    assert detail.status_code == 200
    nested = detail.get_json()['order']['items'][0]['product']
    assert nested['is_discount'] is True
    assert float(nested['price']) == 14.99
    assert float(nested['original_price']) == 16.99

    listed = client.get(
        f'/api/admin/orders?group_deal_id={deal.id}',
        headers=_headers(admin),
    )
    assert listed.status_code == 200
    listed_nested = listed.get_json()['orders'][0]['items'][0]['product']
    assert listed_nested['is_discount'] is True
    assert float(listed_nested['price']) == 14.99
    assert detail.get_json()['order']['buyer_pricing']['influencer'] is False
    assert detail.get_json()['order']['buyer_pricing']['rates'] == {}


def test_customer_patch_reprices_quantity_break_siblings(app, db_session):
    user = _user('+15551111889', '买家')
    deal = _deal()
    product = _product(
        price=10,
        pricing_data={'price': 10, 'quantity_breaks': [{'min_qty': 3, 'price': 8}]},
        cutting_enabled=True,
        cutting_fee=0,
    )
    _link(deal, product, stock=10)
    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(user), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [
            {'product_id': product.id, 'quantity': 2, 'cutting': False},
            {'product_id': product.id, 'quantity': 1, 'cutting': True},
        ],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    items = order['items']
    assert {float(i['unit_price']) for i in items} == {8.0}
    uncut = next(i for i in items if not i['cutting'])

    patched = client.patch(f"/api/orders/{order['id']}", headers=_headers(user), json={
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [{'id': uncut['id'], 'product_id': product.id, 'quantity': 2, 'cutting': False}],
    })
    assert patched.status_code == 200, patched.get_json()
    left = patched.get_json()['order']['items']
    assert len(left) == 1
    assert left[0]['id'] == uncut['id']
    assert float(left[0]['unit_price']) == 10.0
