"""End-to-end payload regressions for batched deal/order/admin queries."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from constants.status_enums import DeliveryMethod, OrderStatus, PaymentStatus, UserStatus
from models import db
from models.address import Address
from models.base import utc_now
from models.groupdeal import GroupDeal, GroupDealProduct
from models.influencer import InfluencerProductRate, InfluencerProfile
from models.order import Order, OrderItem
from models.product import Product
from models.product_category import ProductCategory
from models.product_sales_stats import ProductSalesStats
from models.product_variant import ProductVariant
from models.referral_program import ReferralRecord
from models.supplier import Supplier
from models.user import AuthToken, User, UserRole
from services import influencer_service
from utils.query_batch import products_by_ids, unique_ids
from utils.stock_management import check_and_reserve_stock


def _user(phone, nickname, **kwargs):
    u = User(phone=phone, nickname=nickname, status=UserStatus.ACTIVE.value, **kwargs)
    db.session.add(u)
    db.session.flush()
    return u


def _make_influencer(phone='+15550000001', nickname='官'):
    user = _user(phone, nickname)
    db.session.add(UserRole(user_id=user.id, role='influencer'))
    influencer_service.activate_profile_for_user(user.id)
    db.session.flush()
    return user


def _admin():
    user = _user('+15550000999', 'Admin')
    db.session.add(UserRole(user_id=user.id, role='admin'))
    db.session.flush()
    return user


def _token(user):
    existing = AuthToken.query.filter_by(user_id=user.id, is_revoked=False).first()
    if existing:
        return existing.token
    tok = AuthToken(
        user_id=user.id,
        token=f'tok-qbr-{user.id}-{user.phone}',
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


def _product(name, price=10, **kwargs):
    kwargs.setdefault('is_active', True)
    p = Product(
        name=name,
        pricing_type='per_item',
        pricing_data={'price': price},
        **kwargs,
    )
    db.session.add(p)
    db.session.flush()
    return p


def _order(user, deal, product, qty=1, unit=Decimal('10.00'), **kwargs):
    data = dict(
        user_id=user.id,
        group_deal_id=deal.id,
        order_number=f'TEST-QBR-{user.id}-{product.id}-{qty}-{id(product)}',
        subtotal=unit * qty,
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=unit * qty,
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method=DeliveryMethod.PICKUP.value,
        payment_method='cash',
        payment_status=PaymentStatus.UNPAID.value,
        status=OrderStatus.SUBMITTED.value,
        store_credit_applied=Decimal('0'),
    )
    data.update(kwargs)
    order = Order(**data)
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=qty,
        unit_price=unit,
        total_price=unit * qty,
    ))
    db.session.flush()
    return order


def _assert_product_payload(row, *, expect_category=True, expect_supplier=True):
    assert row['id']
    assert row['name']
    assert 'price' in row
    assert 'pricing_type' in row
    assert 'variants' in row
    assert isinstance(row['variants'], list)
    if expect_category:
        assert row.get('category')
        assert row['category']['name']
    if expect_supplier:
        assert row.get('supplier')
        assert row['supplier']['name']


def test_unique_ids_and_empty_product_prefetch(app):
    assert unique_ids([None, 3, 3, 1, None, 2]) == [3, 1, 2]
    assert products_by_ids([]) == {}
    assert products_by_ids([None]) == {}


def test_deal_list_detail_latest_payloads_and_inactive_filter(app, db_session):
    category = ProductCategory(name='肉', is_active=True)
    supplier = Supplier(name='供应商')
    db_session.add_all([category, supplier])
    db_session.flush()

    deal = _deal()
    empty = _deal(title='空团', order_start_date=datetime(2026, 2, 1))
    active = _product('黑毛猪', price=20, category_id=category.id, supplier_id=supplier.id)
    inactive = _product(
        '下架鹅', price=30, category_id=category.id, supplier_id=supplier.id, is_active=False,
    )
    discounted = _product('特价蛋', price=16, category_id=category.id, supplier_id=supplier.id)
    db_session.add_all([
        ProductVariant(product_id=active.id, name='大', sort_order=0),
        ProductVariant(product_id=active.id, name='小', sort_order=1),
        ProductVariant(product_id=inactive.id, name='默认', sort_order=0),
        ProductVariant(product_id=discounted.id, name='默认', sort_order=0),
        GroupDealProduct(group_deal_id=deal.id, product_id=active.id, deal_stock_limit=8),
        GroupDealProduct(group_deal_id=deal.id, product_id=inactive.id),
        GroupDealProduct(group_deal_id=deal.id, product_id=discounted.id, is_discount=True),
    ])
    db_session.flush()

    client = app.test_client()
    listed = client.get('/api/group-deals')
    assert listed.status_code == 200
    deals = {d['id']: d for d in listed.get_json()['deals']}
    assert empty.id in deals
    assert deals[empty.id]['products'] == []
    listed_ids = [p['id'] for p in deals[deal.id]['products']]
    assert listed_ids == list(dict.fromkeys(listed_ids))
    assert active.id in listed_ids
    assert discounted.id in listed_ids
    assert inactive.id not in listed_ids
    for row in deals[deal.id]['products']:
        _assert_product_payload(row)
    sale = next(p for p in deals[deal.id]['products'] if p['id'] == discounted.id)
    assert sale['is_discount'] is True
    assert sale['sale_price'] is not None

    detail = client.get(f'/api/group-deals/{deal.id}')
    assert detail.status_code == 200
    detail_products = detail.get_json()['deal']['products']
    detail_ids = [p['id'] for p in detail_products]
    assert detail_ids == list(dict.fromkeys(detail_ids))
    assert set(detail_ids) == {active.id, inactive.id, discounted.id}
    pig = next(p for p in detail_products if p['id'] == active.id)
    assert [v['name'] for v in pig['variants']] == ['大', '小']
    _assert_product_payload(pig)

    latest = client.get('/api/group-deals/latest')
    assert latest.status_code == 200
    latest_deal = latest.get_json()['deal']
    assert latest_deal['id'] == empty.id
    assert latest_deal['products'] == []


def test_influencer_catalog_discounts_regular_user_does_not(app, db_session):
    inf = _make_influencer()
    regular = _user('+15550000002', '普通')
    deal = _deal()
    product = _product('鸭', price=16)
    db_session.add_all([
        GroupDealProduct(group_deal_id=deal.id, product_id=product.id),
        InfluencerProductRate(
            product_id=product.id, commission_type='per_item', amount=Decimal('0.25'),
        ),
    ])
    db_session.flush()

    client = app.test_client()
    inf_detail = client.get(f'/api/group-deals/{deal.id}', headers=_headers(inf)).get_json()['deal']
    row = inf_detail['products'][0]
    assert row['influencer_discount'] is True
    assert Decimal(str(row['display_price'])) == Decimal('15.75')
    assert Decimal(str(row['original_price'])) == Decimal('16.00')

    listed = client.get('/api/group-deals', headers=_headers(inf)).get_json()
    listed_row = next(p for d in listed['deals'] if d['id'] == deal.id for p in d['products'])
    assert listed_row['influencer_discount'] is True
    assert Decimal(str(listed_row['display_price'])) == Decimal('15.75')

    regular_detail = client.get(
        f'/api/group-deals/{deal.id}', headers=_headers(regular)
    ).get_json()['deal']['products'][0]
    assert not regular_detail.get('influencer_discount')
    assert Decimal(str(regular_detail['display_price'])) == Decimal('16.00')

    influencer_service.deactivate_profile_for_user(inf.id)
    db_session.flush()
    db_session.expire(inf)
    off = client.get(f'/api/group-deals/{deal.id}', headers=_headers(inf)).get_json()
    assert not off['deal']['products'][0].get('influencer_discount')
    assert Decimal(str(off['deal']['products'][0]['display_price'])) == Decimal('16.00')


def test_product_catalog_include_stats_and_eager_relations(app, db_session):
    category = ProductCategory(name='菜', is_active=True)
    supplier = Supplier(name='农场')
    db_session.add_all([category, supplier])
    db_session.flush()
    product = _product('青菜', price=5, category_id=category.id, supplier_id=supplier.id)
    db_session.add(ProductVariant(product_id=product.id, name='把', sort_order=0))
    db_session.add(ProductSalesStats(
        product_id=product.id,
        sale_date=date.today(),
        quantity_sold=7,
        order_count=3,
    ))
    db_session.flush()

    client = app.test_client()
    res = client.get('/api/products?include_stats=true')
    assert res.status_code == 200
    row = next(p for p in res.get_json()['products'] if p['id'] == product.id)
    _assert_product_payload(row)
    assert row['sales_stats']['total_sold'] == 7
    assert row['sales_stats']['total_orders'] == 3


def test_customer_orders_include_items_address_deal_and_auto_confirm(app, db_session):
    user = _user('+15550000003', '买家')
    deal = _deal(order_end_date=datetime(2026, 1, 2), status='closed')
    product = _product('鸡', price=12)
    address = Address(
        user_id=user.id,
        recipient_name='收件人',
        phone='+14165550111',
        address_line1='1 Main St',
        city='Toronto',
        postal_code='M1M1M1',
    )
    db_session.add(address)
    db_session.flush()
    source = _order(user, deal, product, qty=1, unit=Decimal('12.00'), status=OrderStatus.CANCELLED.value)
    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        address_id=address.id,
        order_number=f'TEST-QBR-MAIN-{user.id}',
        subtotal=Decimal('12.00'),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal('12.00'),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method=DeliveryMethod.DELIVERY.value,
        payment_method='cash',
        payment_status=PaymentStatus.UNPAID.value,
        status=OrderStatus.SUBMITTED.value,
        store_credit_applied=Decimal('0'),
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal('12.00'),
        total_price=Decimal('12.00'),
        source_order_id=source.id,
        source_item_id=source.items[0].id,
    ))
    db.session.flush()

    client = app.test_client()
    listed = client.get('/api/orders', headers=_headers(user))
    assert listed.status_code == 200
    rows = listed.get_json()['orders']
    assert len(rows) == 2
    main = next(o for o in rows if o['id'] == order.id)
    assert main['status'] == OrderStatus.CONFIRMED.value
    assert main['group_deal']['id'] == deal.id
    assert main['group_deal']['title'] == '团'
    assert main['address']['city'] == 'Toronto'
    assert len(main['items']) == 1
    assert main['items'][0]['product']['name'] == '鸡'
    assert main['items'][0]['lineage']['source_order_id'] == source.id
    assert main['items'][0]['lineage']['source_order_number'] == source.order_number

    detail = client.get(f'/api/orders/{order.id}', headers=_headers(user))
    assert detail.status_code == 200
    body = detail.get_json()['order']
    assert body['status'] == OrderStatus.CONFIRMED.value
    assert body['items'][0]['product']['id'] == product.id


def test_checkout_prices_influencer_and_sale_and_collapses_stock(app, db_session):
    inf = _make_influencer(phone='+15550000004')
    deal = _deal()
    product = _product('蛋', price=16)
    db_session.add_all([
        GroupDealProduct(
            group_deal_id=deal.id,
            product_id=product.id,
            is_discount=True,
            deal_stock_limit=5,
        ),
        InfluencerProductRate(
            product_id=product.id, commission_type='per_item', amount=Decimal('1.00'),
        ),
    ])
    product.pricing_data = {'price': 16, 'sale_price': 12}
    db_session.flush()

    client = app.test_client()
    created = client.post('/api/orders', headers=_headers(inf), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [
            {'product_id': product.id, 'quantity': 2},
            {'product_id': product.id, 'quantity': 1},
        ],
    })
    assert created.status_code == 201, created.get_json()
    order = created.get_json()['order']
    assert len(order['items']) == 2
    assert {Decimal(str(i['unit_price'])) for i in order['items']} == {Decimal('11.00')}
    assert Decimal(str(order['subtotal'])) == Decimal('33.00')
    assert order['group_deal']['id'] == deal.id
    assert all(i['product']['name'] == '蛋' for i in order['items'])

    leftover = GroupDealProduct.query.filter_by(
        group_deal_id=deal.id, product_id=product.id,
    ).first()
    assert leftover.deal_stock_limit == 5

    blocked = client.post('/api/orders', headers=_headers(inf), json={
        'group_deal_id': deal.id,
        'delivery_method': 'pickup',
        'payment_method': 'cash',
        'items': [
            {'product_id': product.id, 'quantity': 2},
            {'product_id': product.id, 'quantity': 1},
        ],
    })
    assert blocked.status_code == 400
    assert '库存不足' in (blocked.get_json() or {}).get('error', '')


def test_stock_reserve_empty_and_missing_product(app, db_session):
    deal = _deal()
    ok, err = check_and_reserve_stock(deal.id, [])
    assert ok is True
    assert err is None
    ok, err = check_and_reserve_stock(deal.id, [{'product_id': 999999, 'quantity': 1}])
    assert ok is False
    assert 'not found' in err


def test_admin_orders_users_stats_referrals_payloads(app, db_session):
    admin = _admin()
    inf = _make_influencer(phone='+15550000005', nickname='推荐官甲')
    customer = _user('+15550000006', '客户乙')
    customer.referred_by_user_id = inf.id
    loner = _user('+15550000007', '无单')
    deal = _deal()
    product = _product('鹅', price=40)
    address = Address(
        user_id=customer.id,
        recipient_name='乙',
        phone='+14165550222',
        address_line1='2 King St',
        city='Markham',
        postal_code='L3R1A1',
    )
    db_session.add(address)
    db_session.flush()
    order = Order(
        user_id=customer.id,
        group_deal_id=deal.id,
        address_id=address.id,
        order_number='TEST-QBR-ADMIN-1',
        subtotal=Decimal('40.00'),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal('40.00'),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method=DeliveryMethod.DELIVERY.value,
        payment_method='cash',
        payment_status=PaymentStatus.PAID.value,
        status=OrderStatus.COMPLETED.value,
        store_credit_applied=Decimal('0'),
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal('40.00'),
        total_price=Decimal('40.00'),
    ))
    db.session.add(ReferralRecord(
        inviter_user_id=inf.id,
        invitee_user_id=customer.id,
        status=ReferralRecord.STATUS_REWARDED,
        first_completed_order_id=order.id,
        rewarded_at=utc_now(),
    ))
    db_session.flush()

    client = app.test_client()
    headers = _headers(admin)

    listed = client.get('/api/admin/orders', headers=headers)
    assert listed.status_code == 200
    row = listed.get_json()['orders'][0]
    assert row['user']['nickname'] == '客户乙'
    assert row['group_deal']['id'] == deal.id
    assert row['address']['city'] == 'Markham'
    assert row['items'][0]['product']['name'] == '鹅'
    assert row['items_count'] == 1

    detail = client.get(f'/api/admin/orders/{order.id}', headers=headers)
    assert detail.status_code == 200
    body = detail.get_json()['order']
    assert body['user']['is_influencer'] is False
    assert body['items'][0]['product']['id'] == product.id
    assert body['address']['postal_code'] == 'L3R1A1'
    assert body['group_deal']['title'] == '团'

    users = client.get('/api/admin/users?per_page=50', headers=headers)
    assert users.status_code == 200
    by_id = {u['id']: u for u in users.get_json()['users']}
    assert by_id[customer.id]['order_count'] == 1
    assert by_id[loner.id]['order_count'] == 0
    assert by_id[inf.id]['is_influencer'] is True
    assert by_id[customer.id]['referrer_is_influencer'] is True
    assert by_id[customer.id]['referrer_display_name'] == '推荐官甲'

    stats = client.get('/api/admin/stats', headers=headers)
    assert stats.status_code == 200
    payload = stats.get_json()
    assert payload['stats']['orders'] == 1
    assert payload['stats']['users'] == 4
    assert payload['stats']['products'] == 1
    assert payload['recent_orders'][0]['user_name'] == '客户乙'
    assert payload['recent_orders'][0]['order_number'] == 'TEST-QBR-ADMIN-1'

    referrals = client.get('/api/admin/referrals', headers=headers)
    assert referrals.status_code == 200
    rec = referrals.get_json()['referrals'][0]
    assert rec['inviter']['nickname'] == '推荐官甲'
    assert rec['invitee']['nickname'] == '客户乙'
    assert rec['invitee_has_completed_order'] is True

    admin_deals = client.get('/api/admin/group-deals', headers=headers)
    assert admin_deals.status_code == 200
    full_deal = admin_deals.get_json()['group_deals'][0]
    assert 'products' in full_deal
    lite = client.get('/api/admin/group-deals?include_products=0', headers=headers)
    assert lite.status_code == 200
    assert 'products' not in lite.get_json()['group_deals'][0]


def test_invitees_and_influencer_customers_http(app, db_session):
    inf = _make_influencer(phone='+15550000008', nickname='官丙')
    pending = _user('+15550000009', '未下单丁')
    pending.referred_by_user_id = inf.id
    ordered = _user('+15550000010', '已下单戊')
    ordered.referred_by_user_id = inf.id
    deal = _deal()
    product = _product('菜', price=8)
    _order(ordered, deal, product, qty=1, unit=Decimal('8.00'))
    db_session.add_all([
        ReferralRecord(inviter_user_id=inf.id, invitee_user_id=pending.id),
        ReferralRecord(inviter_user_id=inf.id, invitee_user_id=ordered.id),
    ])
    db_session.flush()

    client = app.test_client()
    invitees = client.get('/api/referrals/invitees', headers=_headers(inf))
    assert invitees.status_code == 200
    rows = {r['invitee_user_id']: r for r in invitees.get_json()['invitees']}
    assert rows[pending.id]['invitee_nickname'] == '未下单丁'
    assert rows[pending.id]['status_label'] == '已绑定，未下单'
    assert rows[ordered.id]['status_label'] == '已下单，待完成'

    customers = client.get('/api/influencer/customers', headers=_headers(inf))
    assert customers.status_code == 200
    body = customers.get_json()['customers']
    assert {c['id'] for c in body} == {pending.id, ordered.id}
    ordered_row = next(c for c in body if c['id'] == ordered.id)
    assert ordered_row['order_count'] == 1
    assert ordered_row['in_progress_order_count'] == 1

    detail = client.get(f'/api/influencer/customers/{ordered.id}', headers=_headers(inf))
    assert detail.status_code == 200
    orders = detail.get_json()['orders']
    assert len(orders) == 1
    assert orders[0]['group_deal_title'] == '团'
    assert orders[0]['items'][0]['product_name'] == '菜'
