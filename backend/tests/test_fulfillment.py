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


def test_fulfillment_can_save_one_weight_without_removing_lines(app):
    staff = _fulfillment(email='weigher@example.com')
    customer = _user('+10000000121', 'CustW')
    deal = _deal('preparing')
    other = _product()
    weighed = Product(
        name='肉',
        pricing_type='unit_weight',
        pricing_data={'price_per_unit': 5, 'unit': 'lb'},
        is_active=True,
    )
    db.session.add(weighed)
    db.session.flush()
    order = _order(customer, deal, other, status=OrderStatus.PREPARING.value)
    line = OrderItem(
        order_id=order.id,
        product_id=weighed.id,
        quantity=1,
        unit_price=Decimal('5'),
        total_price=Decimal('5'),
    )
    db.session.add(line)
    db.session.flush()
    client = app.test_client()

    res = client.put(
        f'/api/admin/orders/{order.id}/update-weights',
        json={'items': [{'item_id': line.id, 'final_weight': 2.5}]},
        headers=_headers(staff),
    )
    assert res.status_code == 200
    items = res.get_json()['order']['items']
    assert len(items) == 2
    saved = next(item for item in items if item['id'] == line.id)
    assert float(saved['final_weight']) == 2.5
    assert float(saved['total_price']) == 12.5
    assert any(item['id'] != line.id for item in items)


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


def test_mark_delivered_unpaid_cash_stays_delivered(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000128', 'CashDue'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
    )
    order.payment_method = 'cash'
    order.payment_status = PaymentStatus.UNPAID.value
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()
    res = app.test_client().post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=_headers(staff),
    )
    assert res.status_code == 200
    db.session.refresh(order)
    assert order.status == OrderStatus.DELIVERED.value
    assert order.payment_status == PaymentStatus.UNPAID.value
    assert order.delivered_at is not None


def test_mark_cash_received_then_delivered_completes(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000129', 'CashFirst'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
    )
    order.payment_method = 'cash'
    order.payment_status = PaymentStatus.UNPAID.value
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()
    client = app.test_client()
    headers = _headers(staff)

    cash = client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-cash-received',
        json={},
        headers=headers,
    )
    assert cash.status_code == 200
    db.session.refresh(order)
    assert order.payment_status == PaymentStatus.PAID.value
    assert order.status == OrderStatus.OUT_FOR_DELIVERY.value

    delivered = client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=headers,
    )
    assert delivered.status_code == 200
    db.session.refresh(order)
    assert order.status == OrderStatus.COMPLETED.value


def test_delivered_then_cash_received_completes(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000130', 'DropFirst'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
    )
    order.payment_method = 'cash'
    order.payment_status = PaymentStatus.UNPAID.value
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()
    client = app.test_client()
    headers = _headers(staff)

    delivered = client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=headers,
    )
    assert delivered.status_code == 200
    cash = client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-cash-received',
        json={},
        headers=headers,
    )
    assert cash.status_code == 200
    db.session.refresh(order)
    assert order.payment_status == PaymentStatus.PAID.value
    assert order.status == OrderStatus.COMPLETED.value


def test_mark_cash_received_rejects_card_order(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000131', 'CardNo'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
    )
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()
    res = app.test_client().post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-cash-received',
        json={},
        headers=_headers(staff),
    )
    assert res.status_code == 400


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
    assert toronto_line['cash_collected'] == 0.0
    assert earnings['totals']['cash_collected'] == 0.0


def test_paid_cash_without_driver_confirm_is_not_collected(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000118', 'OfficeCash'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
        city='Toronto',
    )
    order.payment_method = 'cash'
    order.payment_status = PaymentStatus.PAID.value
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()

    client = app.test_client()
    assert client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=_headers(staff),
    ).status_code == 200

    earnings = fulfillment_service.earnings_for_user(staff.id)
    assert earnings['totals']['cash_collected'] == 0.0
    assert earnings['deliveries'][0]['cash_collected'] == 0.0
    db.session.refresh(order)
    assert order.cash_collected_on_delivery is None


def test_self_delivery_cash_is_separate_from_earnings(app):
    staff = _fulfillment()
    order = _order(
        _user('+10000000117', 'CashCod'),
        _deal('preparing'),
        _product(),
        delivery=True,
        status=OrderStatus.OUT_FOR_DELIVERY.value,
        city='Toronto',
    )
    order.payment_method = 'cash'
    order.payment_status = PaymentStatus.UNPAID.value
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    db.session.commit()

    client = app.test_client()
    headers = _headers(staff)
    assert client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-delivered',
        json={},
        headers=headers,
    ).status_code == 200
    assert client.post(
        f'/api/admin/fulfillment/orders/{order.id}/mark-cash-received',
        json={},
        headers=headers,
    ).status_code == 200

    earnings = fulfillment_service.earnings_for_user(staff.id)
    db.session.refresh(order)
    assert float(order.cash_collected_on_delivery) == 10.0
    assert earnings['totals']['cash_collected'] == 10.0
    assert earnings['totals']['delivery'] == 7.0
    assert earnings['totals']['earned'] == 7.0
    assert earnings['totals']['outstanding'] == 7.0
    assert earnings['deliveries'][0]['cash_collected'] == 10.0
    assert earnings['deliveries'][0]['recipient_name'] == '收件人'
    assert earnings['deliveries'][0]['address'] == '1 Main St, Toronto, M1M1M1'
    assert earnings['deliveries'][0]['payment_label'] == '现金'
    assert earnings['deliveries'][0]['paid_amount'] == 10.0
    cycle = next(row for row in earnings['cycles'] if row['totals']['delivery_count'])
    assert cycle['group_deal_id'] == order.group_deal_id
    assert cycle['totals']['cash_collected'] == 10.0
    assert cycle['totals']['earned'] == 7.0
    assert cycle['totals']['outstanding'] == 7.0
    assert cycle['totals']['paid'] == 0.0
    assert [row['order_id'] for row in cycle['deliveries']] == [order.id]
    assert cycle['deliveries'][0]['fee'] == 7.0
    assert cycle['deliveries'][0]['cash_collected'] == 10.0


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


def test_earnings_cycles_group_by_group_deal(app):
    staff = _fulfillment()
    previous = _deal('completed')
    previous.title = '上一团'
    previous.pickup_date = datetime(2026, 9, 12)
    current = _deal('preparing')
    current.title = '这一团'
    current.pickup_date = datetime(2026, 10, 8)
    previous_session = fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-09-12',
        'start_time': '09:00',
        'end_time': '12:00',
    })
    previous_session.group_deal_id = None
    current_session = fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-10-08',
        'start_time': '11:30',
        'end_time': '15:00',
    })
    order = _order(
        _user('+10000000119', 'DealSettle'),
        previous,
        _product(),
        delivery=True,
        status=OrderStatus.COMPLETED.value,
    )
    fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    order.delivered_at = datetime(2026, 10, 8, 18, 0)
    order.delivery_fee_earned = Decimal('7.00')
    db.session.commit()

    assert current_session.group_deal_id == current.id
    cycles = fulfillment_service.earnings_for_user(staff.id)['cycles']
    by_deal = {row['group_deal_id']: row for row in cycles}
    assert by_deal[previous.id]['group_deal_title'] == '上一团'
    assert by_deal[previous.id]['pickup_date'] == '2026-09-12'
    assert by_deal[previous.id]['totals']['hours'] == 3.0
    assert [row['work_date'] for row in by_deal[previous.id]['sessions']] == ['2026-09-12']
    assert [row['order_id'] for row in by_deal[previous.id]['deliveries']] == [order.id]
    assert by_deal[previous.id]['deliveries'][0]['recipient_name'] == '收件人'
    assert by_deal[previous.id]['deliveries'][0]['payment_label'] == '信用卡'
    assert by_deal[previous.id]['deliveries'][0]['paid_amount'] == 10.0
    assert by_deal[current.id]['is_current'] is True
    assert by_deal[current.id]['totals']['hours'] == 3.5
    assert [row['work_date'] for row in by_deal[current.id]['sessions']] == ['2026-10-08']
    assert by_deal[current.id]['deliveries'] == []
    assert cycles[0]['group_deal_id'] == current.id
    assert by_deal[previous.id]['settled'] is False


def test_admin_can_mark_group_deal_settled(app):
    staff = _fulfillment()
    admin = _admin()
    deal = _deal('completed')
    deal.title = '待结算团'
    profile = fulfillment_service.get_or_create_profile(staff.id)
    profile.hourly_rate = Decimal('20')
    db.session.flush()
    fulfillment_service.create_session(staff.id, staff.id, {
        'work_date': '2026-09-12',
        'start_time': '09:00',
        'end_time': '12:00',
        'group_deal_id': deal.id,
    })
    db.session.commit()

    client = app.test_client()
    marked = client.post(
        '/api/admin/fulfillment/settlements',
        json={'user_id': staff.id, 'group_deal_id': deal.id, 'settled': True},
        headers=_headers(admin),
    )
    assert marked.status_code == 200

    earnings = fulfillment_service.earnings_for_user(staff.id)
    cycle = next(row for row in earnings['cycles'] if row['group_deal_id'] == deal.id)
    assert cycle['settled'] is True
    assert cycle['totals']['outstanding'] == 0.0
    assert cycle['totals']['paid'] == cycle['totals']['labor']
    assert earnings['totals']['paid'] == cycle['totals']['labor']
    assert earnings['totals']['outstanding'] == 0.0

    undone = client.post(
        '/api/admin/fulfillment/settlements',
        json={'user_id': staff.id, 'group_deal_id': deal.id, 'settled': False},
        headers=_headers(admin),
    )
    assert undone.status_code == 200
    earnings = fulfillment_service.earnings_for_user(staff.id)
    cycle = next(row for row in earnings['cycles'] if row['group_deal_id'] == deal.id)
    assert cycle['settled'] is False
    assert cycle['totals']['paid'] == 0.0
    assert cycle['totals']['outstanding'] == cycle['totals']['labor']


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


def test_assign_self_appends_in_add_order(app):
    staff = _fulfillment()
    deal = _deal('preparing')
    product = _product()
    later_postal = _order(
        _user('+10000004101', 'LatePostal'), deal, product, delivery=True, postal_code='M9Z 9Z9'
    )
    earlier_postal = _order(
        _user('+10000004102', 'EarlyPostal'), deal, product, delivery=True, postal_code='A1A 1A1'
    )
    fulfillment_service.assign_delivery(later_postal, DeliveryHandler.SELF.value, staff)
    fulfillment_service.assign_delivery(earlier_postal, DeliveryHandler.SELF.value, staff)
    db.session.commit()

    plan = fulfillment_service.deal_delivery_plan(deal, staff)
    assert [row['id'] for row in plan['self']] == [later_postal.id, earlier_postal.id]
    assert [row['delivery_route_seq'] for row in plan['self']] == [1, 2]


def test_assign_self_appends_after_existing_route(app):
    staff = _fulfillment()
    deal = _deal('preparing')
    product = _product()
    first = _order(_user('+10000004111', 'First'), deal, product, delivery=True, postal_code='M5V 1A1')
    second = _order(_user('+10000004112', 'Second'), deal, product, delivery=True, postal_code='L4C 0A1')
    first.delivery_handler = DeliveryHandler.SELF.value
    first.delivery_route_seq = 1
    second.delivery_handler = DeliveryHandler.SELF.value
    second.delivery_route_seq = 2
    db.session.commit()
    newbie = _order(
        _user('+10000004113', 'Newbie'), deal, product, delivery=True, postal_code='A1A 1A1'
    )
    fulfillment_service.assign_delivery(newbie, DeliveryHandler.SELF.value, staff)
    fulfillment_service.assign_delivery(first, DeliveryHandler.SELF.value, staff)
    db.session.commit()

    plan = fulfillment_service.deal_delivery_plan(deal, staff)
    assert [row['id'] for row in plan['self']] == [first.id, second.id, newbie.id]
    assert [row['delivery_route_seq'] for row in plan['self']] == [1, 2, 3]


def test_leaving_self_compacts_route_seq(app):
    staff = _fulfillment()
    deal = _deal('preparing')
    product = _product()
    first = _order(_user('+10000004121', 'One'), deal, product, delivery=True, postal_code='M9Z 9Z9')
    middle = _order(_user('+10000004122', 'Two'), deal, product, delivery=True, postal_code='A1A 1A1')
    last = _order(_user('+10000004123', 'Three'), deal, product, delivery=True, postal_code='L4C 0A1')
    for order in (first, middle, last):
        fulfillment_service.assign_delivery(order, DeliveryHandler.SELF.value, staff)
    fulfillment_service.assign_delivery(middle, DeliveryHandler.UNASSIGNED.value, staff)
    db.session.commit()

    plan = fulfillment_service.deal_delivery_plan(deal, staff)
    assert [row['id'] for row in plan['self']] == [first.id, last.id]
    assert [row['delivery_route_seq'] for row in plan['self']] == [1, 2]
    db.session.refresh(middle)
    assert middle.delivery_route_seq is None

    fulfillment_service.assign_delivery(last, DeliveryHandler.THIRD_PARTY.value, staff, 'FlashBox')
    db.session.commit()
    plan = fulfillment_service.deal_delivery_plan(deal, staff)
    assert [row['id'] for row in plan['self']] == [first.id]
    assert plan['self'][0]['delivery_route_seq'] == 1
    db.session.refresh(last)
    assert last.delivery_route_seq is None


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
