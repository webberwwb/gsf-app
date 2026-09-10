"""Fulfillment role: RBAC, PII lock, delivery assignment, timesheets, login."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from constants.status_enums import DeliveryHandler, DeliveryMethod, OrderStatus, PaymentStatus, UserStatus
from models import db
from models.address import Address
from models.base import utc_now
from models.fulfillment import FulfillmentProfile
from models.groupdeal import GroupDeal
from models.order import Order, OrderItem
from models.product import Product
from models.user import AuthToken, User, UserRole
from services import fulfillment_service


def _user(phone, nickname, email=None, **kwargs):
    u = User(
        phone=phone,
        nickname=nickname,
        email=email,
        status=UserStatus.ACTIVE.value,
        **kwargs,
    )
    db.session.add(u)
    db.session.flush()
    return u


def _admin():
    user = _user('+10000000991', 'Admin', email='admin-test@example.com')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.flush()
    return user


def _fulfillment(email='packer@example.com', phone=None):
    user = _user(phone or f'+10000000{abs(hash(email)) % 10000:04d}', 'Packer', email=email)
    db.session.add(UserRole(user_id=user.id, role='fulfillment'))
    fulfillment_service.activate_profile_for_user(user.id)
    db.session.flush()
    return user


def _token(user):
    existing = AuthToken.query.filter_by(user_id=user.id, is_revoked=False).first()
    if existing:
        return existing.token
    tok = AuthToken(
        user_id=user.id,
        token=f'tok-{user.id}-{user.phone}',
        token_type='bearer',
        expires_at=utc_now() + timedelta(days=1),
    )
    db.session.add(tok)
    db.session.flush()
    return tok.token


def _headers(user):
    return {'Authorization': f'Bearer {_token(user)}'}


def _deal(status='preparing'):
    deal = GroupDeal(
        title='Deal',
        order_start_date=datetime(2026, 1, 1),
        order_end_date=datetime(2026, 12, 31),
        pickup_date=datetime(2026, 6, 1),
        status=status,
    )
    db.session.add(deal)
    db.session.flush()
    return deal


def _product():
    p = Product(name='菜', pricing_type='per_item', pricing_data={'price': 10}, is_active=True)
    db.session.add(p)
    db.session.flush()
    return p


def _order(user, deal, product, delivery=False, status=OrderStatus.PREPARING.value, city='Toronto', postal_code='M1M1M1'):
    address = None
    if delivery:
        address = Address(
            user_id=user.id,
            recipient_name='收件人',
            phone='+14165550100',
            address_line1='1 Main St',
            city=city,
            postal_code=postal_code,
        )
        db.session.add(address)
        db.session.flush()
    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        address_id=address.id if address else None,
        order_number=f'TEST-FUL-{user.id}-{deal.id}-{product.id}',
        subtotal=Decimal('10.00'),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal('10.00'),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method=DeliveryMethod.DELIVERY.value if delivery else DeliveryMethod.PICKUP.value,
        payment_method='card' if delivery else 'cash',
        payment_status=PaymentStatus.PAID.value if delivery else PaymentStatus.UNPAID.value,
        status=status,
        store_credit_applied=Decimal('0'),
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal('10.00'),
        total_price=Decimal('10.00'),
    ))
    db.session.flush()
    return order


def test_fulfillment_forbidden_on_admin_only_routes(app):
    staff = _fulfillment()
    client = app.test_client()
    headers = _headers(staff)
    assert client.get('/api/admin/users', headers=headers).status_code == 403
    assert client.get('/api/admin/sdrs', headers=headers).status_code == 403
    assert client.post('/api/admin/group-deals', json={
        'title': 'x',
        'order_start_date': '2026-01-01T00:00:00',
        'order_end_date': '2026-01-02T00:00:00',
        'pickup_date': '2026-01-03T00:00:00',
        'products': [],
    }, headers=headers).status_code == 403


def test_fulfillment_can_list_and_update_weights(app):
    staff = _fulfillment()
    customer = _user('+10000000111', 'Cust')
    deal = _deal('preparing')
    product = _product()
    order = _order(customer, deal, product, status=OrderStatus.PREPARING.value)
    client = app.test_client()
    headers = _headers(staff)

    listed = client.get(f'/api/admin/orders?group_deal_id={deal.id}', headers=headers)
    assert listed.status_code == 200
    assert listed.get_json()['orders'][0]['user']['phone'] == customer.phone

    addrs = client.get(f'/api/admin/users/{customer.id}/addresses', headers=headers)
    assert addrs.status_code == 200
    assert 'addresses' in addrs.get_json()

    trail = client.get(f'/api/admin/orders/{order.id}/audit-trail', headers=headers)
    assert trail.status_code == 200

    res = client.put(f'/api/admin/orders/{order.id}/status', json={'status': 'packing_complete'}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()['order']['status'] == 'packing_complete'


def test_completed_deal_redacts_pii_and_blocks_updates(app):
    staff = _fulfillment()
    customer = _user('+10000000112', 'Cust2', email='c2@example.com')
    customer.wechat = 'wx-secret'
    deal = _deal('completed')
    product = _product()
    order = _order(customer, deal, product, delivery=True, status=OrderStatus.COMPLETED.value)
    client = app.test_client()
    headers = _headers(staff)

    listed = client.get(f'/api/admin/orders?group_deal_id={deal.id}', headers=headers)
    assert listed.status_code == 200
    row = listed.get_json()['orders'][0]
    assert row['pii_locked'] is True
    locked_addrs = client.get(f'/api/admin/users/{customer.id}/addresses', headers=headers)
    assert locked_addrs.status_code == 403
    assert row['user']['phone'] is None
    assert row['user']['wechat'] is None
    assert row['address']['address_line1'] is None

    blocked = client.put(
        f'/api/admin/orders/{order.id}/status',
        json={'status': 'packing_complete'},
        headers=headers,
    )
    assert blocked.status_code == 403


def test_mark_delivered_does_not_require_photo(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000118', 'NoPhoto'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
    )
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()
    res = app.test_client().post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=_headers(staff),
    )
    assert res.status_code == 200
    db.session.refresh(order)
    assert order.status == OrderStatus.COMPLETED.value
    assert order.delivery_photo_url is None


def test_save_delivery_photo_persists_and_can_retake(app):
    staff = _fulfillment()
    customer = _user('+10000000119', 'PhotoCust')
    deal = _deal('preparing')
    product = _product()
    order = _order(customer, deal, product, delivery=True, status=OrderStatus.OUT_FOR_DELIVERY.value)
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()
    client = app.test_client()
    headers = _headers(staff)

    first = client.put(
        f'/api/admin/fulfillment/orders/{order.id}/photo',
        json={'photo_url': 'https://example.com/first.jpg'},
        headers=headers,
    )
    assert first.status_code == 200
    assert first.get_json()['order']['delivery_photo_url'] == 'https://example.com/first.jpg'

    second = client.put(
        f'/api/admin/fulfillment/orders/{order.id}/photo',
        json={'photo_url': 'https://example.com/retake.jpg'},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.get_json()['order']['delivery_photo_url'] == 'https://example.com/retake.jpg'
    db.session.refresh(order)
    assert order.delivery_photo_url == 'https://example.com/retake.jpg'
    assert order.status == OrderStatus.OUT_FOR_DELIVERY.value

    removed = client.delete(
        f'/api/admin/fulfillment/orders/{order.id}/photo',
        headers=headers,
    )
    assert removed.status_code == 200
    assert removed.get_json()['order']['delivery_photo_url'] is None
    db.session.refresh(order)
    assert order.delivery_photo_url is None


def test_delivery_fee_for_address(app):
    assert fulfillment_service.delivery_fee_for_address(None) == Decimal('7.00')
    assert fulfillment_service.delivery_fee_for_address(Address(city='Toronto')) == Decimal('7.00')
    assert fulfillment_service.delivery_fee_for_address(Address(city='Markham')) == Decimal('6.00')
    assert fulfillment_service.delivery_fee_for_address(Address(city='richmond hill')) == Decimal('6.00')
    assert fulfillment_service.delivery_fee_rates() == {
        'nearby_cities': ['Markham', 'Richmond Hill'],
        'nearby_fee': 6.0,
        'other_fee': 7.0,
    }


def test_self_delivery_earns_fee_third_party_does_not(app):
    staff = _fulfillment()
    customer = _user('+10000000113', 'Cust3')
    deal = _deal('preparing')
    product = _product()
    toronto = _order(
        customer, deal, product, delivery=True, status=OrderStatus.OUT_FOR_DELIVERY.value, city='Toronto'
    )
    markham = _order(
        _user('+10000000115', 'Cust5'),
        deal,
        product,
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
        city='Markham',
    )
    other = _order(
        _user('+10000000114', 'Cust4'),
        deal,
        product,
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
    )
    other.order_number = 'TEST-FUL-OTHER'
    fulfillment_service.assign_delivery(toronto, DeliveryHandler.SELF.value, staff)
    fulfillment_service.assign_delivery(markham, DeliveryHandler.SELF.value, staff)
    fulfillment_service.assign_delivery(other, DeliveryHandler.THIRD_PARTY.value, staff, 'FlashBox')
    db.session.commit()

    client = app.test_client()
    headers = _headers(staff)
    assert client.post(
        f'/api/admin/fulfillment/orders/{toronto.id}/mark-delivered',
        json={'photo_url': 'https://example.com/p.jpg'},
        headers=headers,
    ).status_code == 200
    assert client.post(
        f'/api/admin/fulfillment/orders/{markham.id}/mark-delivered',
        json={},
        headers=headers,
    ).status_code == 200
    third = client.post(
        f'/api/admin/fulfillment/orders/{other.id}/mark-delivered',
        json={},
        headers=headers,
    )
    assert third.status_code == 200

    earnings = fulfillment_service.earnings_for_user(staff.id)
    assert earnings['totals']['delivery_count'] == 2
    assert earnings['totals']['delivery'] == 13.0
    fees = {row['city']: row['fee'] for row in earnings['deliveries']}
    assert fees['Toronto'] == 7.0
    assert fees['Markham'] == 6.0
    toronto_line = next(row for row in earnings['deliveries'] if row['city'] == 'Toronto')
    assert toronto_line['suggested_fee'] == 7.0
    assert toronto_line['fee_overridden'] is False


def test_admin_can_override_driver_delivery_fee(app):
    staff = _fulfillment()
    admin = _admin()
    deal = _deal('preparing')
    product = _product()
    order = _order(
        _user('+10000000116', 'Cust6'),
        deal,
        product,
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
        city='Toronto',
    )
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()

    client = app.test_client()
    assert client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=_headers(staff),
    ).status_code == 200

    denied = client.put(
        f'/api/admin/fulfillment/orders/{order.id}/driver-fee',
        json={'amount': 6},
        headers=_headers(staff),
    )
    assert denied.status_code == 403

    fixed = client.put(
        f'/api/admin/fulfillment/orders/{order.id}/driver-fee',
        json={'amount': 6},
        headers=_headers(admin),
    )
    assert fixed.status_code == 200
    assert fixed.get_json()['delivery_fee_earned'] == 6.0
    assert fixed.get_json()['delivery']['fee_overridden'] is True

    earnings = fulfillment_service.earnings_for_user(staff.id)
    assert earnings['totals']['delivery'] == 6.0
    assert earnings['deliveries'][0]['fee'] == 6.0
    assert earnings['deliveries'][0]['suggested_fee'] == 7.0
    assert earnings['deliveries'][0]['fee_overridden'] is True


def test_biweekly_billing_next_pay_date(app):
    sep9 = fulfillment_service.biweekly_billing(date(2026, 9, 9))
    assert sep9['cycle'] == 'biweekly'
    assert sep9['next_pay_date'] == '2026-09-11'
    assert sep9['next_pay_weekday'] == '周五'
    assert sep9['period_start'] == '2026-08-29'
    assert sep9['period_end'] == '2026-09-11'

    payday = fulfillment_service.biweekly_billing(date(2026, 9, 11))
    assert payday['next_pay_date'] == '2026-09-11'
    assert payday['is_payday'] is True

    after = fulfillment_service.biweekly_billing(date(2026, 9, 12))
    assert after['next_pay_date'] == '2026-09-25'

    before_anchor = fulfillment_service.biweekly_billing(date(2026, 8, 20))
    assert before_anchor['next_pay_date'] == '2026-08-28'
    assert before_anchor['period_start'] == '2026-08-15'
    assert before_anchor['period_end'] == '2026-08-28'


def test_earnings_cycles_group_by_pay_period(app):
    staff = _fulfillment()
    fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-08-20',
        'start_time': '16:00',
        'end_time': '18:00',
    })
    fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-09-06',
        'start_time': '16:00',
        'end_time': '19:00',
    })
    db.session.commit()

    cycles = fulfillment_service.earnings_for_user(staff.id)['cycles']
    by_end = {row['period_end']: row for row in cycles}
    assert '2026-08-28' in by_end
    assert '2026-09-11' in by_end
    assert by_end['2026-08-28']['pay_date'] == '2026-08-28'
    assert by_end['2026-08-28']['totals']['hours'] == 2.0
    assert by_end['2026-09-11']['totals']['hours'] == 3.0
    current_end = fulfillment_service.biweekly_billing()['period_end']
    assert by_end[current_end]['is_current'] is True


def test_timesheet_hours_and_ownership(app):
    staff = _fulfillment()
    other = _fulfillment(email='other@example.com')
    session = fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-09-06',
        'start_time': '16:00',
        'end_time': '19:00',
        'notes': '周六配货',
    })
    db.session.commit()
    assert float(session.hours) == 3.0
    assert session.minutes == 180
    assert float(session.labor_amount) == 0.0

    profile = FulfillmentProfile.query.filter_by(user_id=staff.id).first()
    profile.hourly_rate = Decimal('18')
    db.session.flush()
    partial = fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-09-06',
        'start_time': '16:00',
        'end_time': '17:20',
        'notes': '80分钟',
    })
    db.session.commit()
    assert partial.minutes == 80
    assert float(partial.labor_amount) == 24.0

    client = app.test_client()
    res = client.patch(
        f'/api/admin/fulfillment/work-sessions/{session.id}',
        json={'end_time': '20:00'},
        headers=_headers(other),
    )
    assert res.status_code == 403


def test_dev_login_requires_db_role(app):
    privileged = _admin()
    stranger = _user('+10000000130', 'Nope', email='stranger@example.com')
    client = app.test_client()

    denied = client.post('/api/auth/dev-login', json={'email': stranger.email})
    assert denied.status_code == 403

    ok = client.post('/api/auth/dev-login', json={'email': privileged.email})
    assert ok.status_code == 200
    assert ok.get_json().get('token') or ok.get_json().get('user')


def test_assign_fulfillment_role_creates_profile(app):
    admin = _admin()
    user = _user('+10000000140', 'NewStaff', email='newstaff@example.com')
    client = app.test_client()
    res = client.post(
        f'/api/admin/users/{user.id}/roles',
        json={'role': 'fulfillment'},
        headers=_headers(admin),
    )
    assert res.status_code == 200
    db.session.refresh(user)
    assert user.is_fulfillment
    assert FulfillmentProfile.query.filter_by(user_id=user.id).first() is not None


def test_delivery_plan_sorts_by_postal_code(app):
    staff = _fulfillment()
    deal = _deal('preparing')
    product = _product()
    late = _user('+10000004001', 'Late')
    early = _user('+10000004002', 'Early')
    mid = _user('+10000004003', 'Mid')
    _order(late, deal, product, delivery=True, postal_code='L5B 1M5')
    _order(early, deal, product, delivery=True, postal_code='m5v 2t6')
    _order(mid, deal, product, delivery=True, postal_code='L4C0A1')
    db.session.commit()

    plan = fulfillment_service.deal_delivery_plan(deal, staff)
    assert [row['address']['postal_code'] for row in plan['unassigned']] == [
        'L4C0A1',
        'L5B 1M5',
        'm5v 2t6',
    ]


def test_delivery_plan_self_keeps_route_seq(app):
    staff = _fulfillment()
    deal = _deal('preparing')
    product = _product()
    first = _order(_user('+10000004011', 'A'), deal, product, delivery=True, postal_code='M5V 1A1')
    second = _order(_user('+10000004012', 'B'), deal, product, delivery=True, postal_code='L4C 0A1')
    first.delivery_handler = DeliveryHandler.SELF.value
    first.delivery_route_seq = 1
    second.delivery_handler = DeliveryHandler.SELF.value
    second.delivery_route_seq = 2
    db.session.commit()

    plan = fulfillment_service.deal_delivery_plan(deal, staff)
    assert [row['id'] for row in plan['self']] == [first.id, second.id]


def test_deal_delivery_plan_avoids_n_plus_one(app):
    from sqlalchemy import event

    staff = _fulfillment()
    deal = _deal('preparing')
    product = _product()
    order_count = 12
    for i in range(order_count):
        customer = _user(f'+10000003{i:03d}', f'Cust{i}')
        _order(customer, deal, product, delivery=True)
    db.session.commit()

    deal_id = deal.id
    viewer_id = staff.id
    db.session.expire_all()
    deal = GroupDeal.query.get(deal_id)
    viewer = User.query.get(viewer_id)

    statements = []

    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, 'before_cursor_execute', _before_cursor_execute)
    try:
        plan = fulfillment_service.deal_delivery_plan(deal, viewer)
    finally:
        event.remove(db.engine, 'before_cursor_execute', _before_cursor_execute)

    assert len(plan['unassigned']) == order_count
    assert plan['unassigned'][0]['items'][0]['name'] == '菜'
    # orders+users, addresses, items, products, plus viewer.roles — constant vs order count
    assert len(statements) <= 8


def test_group_deals_can_omit_products(app):
    staff = _fulfillment()
    _deal('preparing')
    client = app.test_client()
    lite = client.get('/api/admin/group-deals?include_products=0', headers=_headers(staff))
    assert lite.status_code == 200
    assert 'products' not in lite.get_json()['group_deals'][0]

    full = client.get('/api/admin/group-deals', headers=_headers(staff))
    assert full.status_code == 200
    assert 'products' in full.get_json()['group_deals'][0]


def test_fulfillment_cannot_see_draft_group_deals(app):
    staff = _fulfillment()
    admin = _admin()
    draft = _deal('draft')
    live = _deal('preparing')
    client = app.test_client()

    staff_res = client.get('/api/admin/group-deals', headers=_headers(staff))
    assert staff_res.status_code == 200
    staff_ids = {deal['id'] for deal in staff_res.get_json()['group_deals']}
    assert live.id in staff_ids
    assert draft.id not in staff_ids

    admin_res = client.get('/api/admin/group-deals', headers=_headers(admin))
    assert admin_res.status_code == 200
    admin_ids = {deal['id'] for deal in admin_res.get_json()['group_deals']}
    assert draft.id in admin_ids
    assert live.id in admin_ids

    assert client.get(f'/api/admin/group-deals/{draft.id}', headers=_headers(staff)).status_code == 404
    assert client.get(f'/api/admin/group-deals/{draft.id}', headers=_headers(admin)).status_code == 200
