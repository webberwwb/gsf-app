"""推荐官 bind, rates, accrual, payout, reverse, and RBAC."""
from datetime import datetime, timedelta
from decimal import Decimal

from constants.status_enums import DeliveryMethod, OrderStatus, PaymentStatus, UserStatus
from models import db
from models.groupdeal import GroupDeal, GroupDealProduct, deal_product_to_dict
from models.influencer import (
    PAYOUT_CASH,
    PAYOUT_CREDIT,
    STATUS_CREDITED,
    STATUS_PAYABLE,
    STATUS_REVERSED,
    InfluencerCommissionEntry,
    InfluencerProductRate,
    InfluencerProfile,
    InfluencerProgramConfig,
    InfluencerRateOverride,
)
from models.order import Order, OrderItem
from models.product import Product
from models.sdr import CommissionRecord, CommissionRule, SDR
from models.user import AuthToken, User, UserRole
from models.base import utc_now
from services import influencer_service, referral_service
from services.credit_service import TX_INFLUENCER_LEAD_BONUS, TX_REFERRAL_INVITEE
from models.credit_transaction import CreditTransaction
from utils.order_payment import mark_order_paid


def _user(phone, nickname, **kwargs):
    u = User(phone=phone, nickname=nickname, status=UserStatus.ACTIVE.value, **kwargs)
    db.session.add(u)
    db.session.flush()
    return u


def _make_influencer(phone='+10000000001', nickname='官', payout=PAYOUT_CREDIT):
    user = _user(phone, nickname)
    db.session.add(UserRole(user_id=user.id, role='influencer'))
    influencer_service.activate_profile_for_user(user.id)
    profile = InfluencerProfile.query.filter_by(user_id=user.id).first()
    profile.payout_type = payout
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


def _deal():
    deal = GroupDeal(
        title='Deal',
        order_start_date=datetime(2026, 1, 1),
        order_end_date=datetime(2026, 12, 31),
        pickup_date=datetime(2026, 6, 1),
        status='active',
    )
    db.session.add(deal)
    db.session.flush()
    return deal


def _product(name='鸭', price=20):
    p = Product(name=name, pricing_type='per_item', pricing_data={'price': price}, is_active=True)
    db.session.add(p)
    db.session.flush()
    return p


def _order(user, deal, product, qty=2, unit=Decimal('10.00')):
    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        order_number=f'TEST-INF-{user.id}-{product.id}-{qty}',
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


def test_role_assign_creates_profile_and_code(app, db_session):
    user = _user('+10000000010', 'New')
    influencer_service.activate_profile_for_user(user.id)
    db.session.add(UserRole(user_id=user.id, role='influencer'))
    db_session.flush()
    profile = InfluencerProfile.query.filter_by(user_id=user.id).first()
    assert profile is not None
    assert profile.is_active is True
    assert user.referral_code
    influencer_service.deactivate_profile_for_user(user.id)
    db_session.flush()
    assert InfluencerProfile.query.filter_by(user_id=user.id).first().is_active is False
    assert user.is_influencer is False


def test_bind_influencer_grants_lead_bonus_not_friend_bonus(app, db_session):
    inf = _make_influencer()
    InfluencerProgramConfig.query.delete()
    db_session.add(InfluencerProgramConfig(lead_bonus_amount=Decimal('7'), is_active=True))
    db_session.flush()
    customer = _user('+10000000011', 'C1')
    ok, err = referral_service.try_bind_referral(customer, inf.referral_code)
    assert ok and err is None
    assert customer.referred_by_user_id == inf.id
    assert Decimal(str(customer.store_credit_balance)) == Decimal('7')
    txs = CreditTransaction.query.filter_by(user_id=customer.id).all()
    assert any(t.tx_type == TX_INFLUENCER_LEAD_BONUS for t in txs)
    assert not any(t.tx_type == TX_REFERRAL_INVITEE for t in txs)


def test_bind_friend_still_uses_invitee_bonus(app, db_session):
    friend = _user('+10000000012', 'Friend', referral_code='FRIEND01')
    customer = _user('+10000000013', 'C2')
    ok, err = referral_service.try_bind_referral(customer, 'FRIEND01')
    assert ok and err is None
    txs = CreditTransaction.query.filter_by(user_id=customer.id).all()
    assert any(t.tx_type == TX_REFERRAL_INVITEE for t in txs)
    assert not any(t.tx_type == TX_INFLUENCER_LEAD_BONUS for t in txs)


def test_admin_reassign_does_not_grant_bonus(app, db_session):
    inf = _make_influencer()
    customer = _user('+10000000014', 'C3')
    customer.referred_by_user_id = inf.id
    db_session.flush()
    assert Decimal(str(customer.store_credit_balance or 0)) == Decimal('0')


def test_skip_influencer_first_order_inviter_reward(app, db_session):
    inf = _make_influencer()
    customer = _user('+10000000015', 'C4')
    ok, _ = referral_service.try_bind_referral(customer, inf.referral_code)
    assert ok
    before = Decimal(str(inf.store_credit_balance or 0))
    deal = _deal()
    product = _product()
    order = _order(customer, deal, product)
    mark_order_paid(order)
    db_session.flush()
    from models.referral_program import ReferralRecord
    rec = ReferralRecord.query.filter_by(invitee_user_id=customer.id).first()
    assert rec.status == ReferralRecord.STATUS_REWARDED
    # no extra first-order inviter reward (commission may still credit)
    friend_reward_txs = CreditTransaction.query.filter_by(
        user_id=inf.id,
        tx_type='referral_inviter_reward',
    ).all()
    assert friend_reward_txs == []


def test_accrual_global_and_override(app, db_session):
    inf = _make_influencer()
    customer = _user('+10000000016', 'C5')
    customer.referred_by_user_id = inf.id
    product = _product('鸡')
    db_session.add(InfluencerProductRate(
        product_id=product.id,
        commission_type='per_item',
        amount=Decimal('2.00'),
    ))
    db_session.flush()
    deal = _deal()
    order = _order(customer, deal, product, qty=3)
    mark_order_paid(order)
    db_session.flush()
    entry = InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()
    assert entry is not None
    assert entry.status == STATUS_CREDITED
    assert Decimal(str(entry.amount)) == Decimal('6.00')
    assert Decimal(str(inf.store_credit_balance)) == Decimal('6.00')

    db_session.add(InfluencerRateOverride(
        influencer_user_id=inf.id,
        product_id=product.id,
        commission_type='per_item',
        amount=Decimal('5.00'),
    ))
    customer2 = _user('+10000000017', 'C6')
    customer2.referred_by_user_id = inf.id
    db_session.flush()
    order2 = _order(customer2, deal, product, qty=2)
    mark_order_paid(order2)
    db_session.flush()
    entry2 = InfluencerCommissionEntry.query.filter_by(order_id=order2.id).first()
    assert Decimal(str(entry2.amount)) == Decimal('10.00')


def test_accrual_skips_orders_before_start_deal(app, db_session):
    inf = _make_influencer(phone='+10000000030')
    profile = InfluencerProfile.query.filter_by(user_id=inf.id).first()
    old_deal = _deal()
    old_deal.title = 'Old'
    new_deal = GroupDeal(
        title='New',
        order_start_date=datetime(2026, 2, 1),
        order_end_date=datetime(2026, 12, 31),
        pickup_date=datetime(2026, 7, 1),
        status='active',
    )
    db_session.add(new_deal)
    db_session.flush()
    profile.commission_from_group_deal_id = new_deal.id
    customer = _user('+10000000031', 'CStart')
    customer.referred_by_user_id = inf.id
    product = _product('羊排')
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('2.00'),
    ))
    db_session.flush()
    old_order = _order(customer, old_deal, product, qty=1)
    old_order.order_number = 'TEST-INF-OLD-DEAL'
    mark_order_paid(old_order)
    db_session.flush()
    assert InfluencerCommissionEntry.query.filter_by(order_id=old_order.id).first() is None

    new_order = _order(customer, new_deal, product, qty=1)
    new_order.order_number = 'TEST-INF-NEW-DEAL'
    mark_order_paid(new_order)
    db_session.flush()
    entry = InfluencerCommissionEntry.query.filter_by(order_id=new_order.id).first()
    assert entry is not None
    assert Decimal(str(entry.amount)) == Decimal('2.00')


def test_cash_payout_and_no_double_accrual(app, db_session):
    inf = _make_influencer(phone='+10000000018', payout=PAYOUT_CASH)
    customer = _user('+10000000019', 'C7')
    customer.referred_by_user_id = inf.id
    product = _product('鹅')
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('1.50'),
    ))
    db_session.flush()
    order = _order(customer, _deal(), product, qty=2)
    mark_order_paid(order)
    db_session.flush()
    entry = InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()
    assert entry.status == STATUS_PAYABLE
    assert Decimal(str(inf.store_credit_balance or 0)) == Decimal('0')
    mark_order_paid(order)
    db_session.flush()
    assert InfluencerCommissionEntry.query.filter_by(order_id=order.id).count() == 1


def test_dashboard_paid_completed_lifetime_and_balance(app, db_session):
    inf = _make_influencer(phone='+10000000026', payout=PAYOUT_CASH)
    customer = _user('+10000000027', 'C9')
    customer.referred_by_user_id = inf.id
    product = _product('羊')
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('2.00'),
    ))
    db_session.flush()
    deal = _deal()
    unpaid = _order(customer, deal, product, qty=1, unit=Decimal('15.00'))
    unpaid.order_number = 'TEST-INF-UNPAID'
    paid = _order(customer, deal, product, qty=2, unit=Decimal('15.00'))
    mark_order_paid(paid)
    db_session.flush()

    dash = influencer_service.dashboard_for(inf.id)
    assert dash['customer_count'] == 1
    assert dash['order_count'] == 1
    assert Decimal(str(dash['customer_order_total'])) == Decimal('30.00')
    assert Decimal(str(dash['lifetime_earnings'])) == Decimal('4.00')
    assert Decimal(str(dash['account_balance'])) == Decimal('4.00')

    entry = InfluencerCommissionEntry.query.filter_by(order_id=paid.id).first()
    influencer_service.mark_cash_paid([entry.id], inf.id)
    db_session.flush()
    dash2 = influencer_service.dashboard_for(inf.id)
    assert Decimal(str(dash2['lifetime_earnings'])) == Decimal('4.00')
    assert Decimal(str(dash2['account_balance'])) == Decimal('0')
    assert dash2['order_count'] == 1


def test_accrual_waits_until_paid_and_completed(app, db_session):
    inf = _make_influencer(phone='+10000000060')
    customer = _user('+10000000061', 'CPaidFirst')
    customer.referred_by_user_id = inf.id
    product = _product('鸭腿')
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('2.00'),
    ))
    db_session.flush()
    order = _order(customer, _deal(), product, qty=2)
    order.payment_status = PaymentStatus.PAID.value
    order.status = OrderStatus.SUBMITTED.value
    db_session.flush()

    assert influencer_service.accrue_for_order(order) is None
    assert InfluencerCommissionEntry.query.filter_by(order_id=order.id).first() is None
    dash = influencer_service.dashboard_for(inf.id)
    assert dash['order_count'] == 0
    assert Decimal(str(dash['lifetime_earnings'])) == Decimal('0')
    assert Decimal(str(dash['account_balance'])) == Decimal('0')

    order.status = OrderStatus.COMPLETED.value
    entry = influencer_service.accrue_for_order(order)
    db_session.flush()
    assert entry is not None
    assert Decimal(str(entry.amount)) == Decimal('4.00')
    assert Decimal(str(inf.store_credit_balance)) == Decimal('4.00')

    dash = influencer_service.dashboard_for(inf.id)
    assert dash['order_count'] == 1
    assert Decimal(str(dash['customer_order_total'])) == Decimal('20.00')
    assert Decimal(str(dash['lifetime_earnings'])) == Decimal('4.00')
    assert Decimal(str(dash['account_balance'])) == Decimal('4.00')

    customers = influencer_service.customers_for(inf.id)
    assert Decimal(str(customers[0]['commission'])) == Decimal('4.00')
    detail = influencer_service.customer_detail_for(inf.id, customer.id)
    item = detail['orders'][0]['items'][0]
    assert item['commission_estimated'] is False
    assert Decimal(str(item['commission_amount'])) == Decimal('4.00')
    assert Decimal(str(detail['orders'][0]['commission']['amount'])) == Decimal('4.00')


def test_weigh_after_paid_complete_refreshes_earnings_and_breakdown(app, db_session):
    inf = _make_influencer(phone='+10000000062')
    customer = _user('+10000000063', 'CWeigh')
    customer.referred_by_user_id = inf.id
    product = Product(
        name='羊腿称重',
        pricing_type='bundled_weight',
        pricing_data={'price_per_unit': 5, 'unit': 'lb', 'min_weight': 7, 'max_weight': 15},
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_weight', amount=Decimal('1.50'),
    ))
    db_session.flush()
    order = _order(customer, _deal(), product, qty=1, unit=Decimal('5.00'))
    mark_order_paid(order)
    db_session.flush()
    assert InfluencerCommissionEntry.query.filter_by(order_id=order.id).first() is None
    dash = influencer_service.dashboard_for(inf.id)
    assert dash['order_count'] == 1
    assert Decimal(str(dash['lifetime_earnings'])) == Decimal('0')

    order.items[0].final_weight = Decimal('9.250')
    from utils.order_totals import sync_order_pricing
    sync_order_pricing(order, reprice_lines=False)
    db_session.flush()

    entry = InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()
    assert entry is not None
    assert Decimal(str(entry.amount)) == Decimal('13.88')
    assert Decimal(str(inf.store_credit_balance)) == Decimal('13.88')
    assert entry.details[0]['weight'] == 9.25
    assert Decimal(str(entry.details[0]['commission'])) == Decimal('13.88')

    dash = influencer_service.dashboard_for(inf.id)
    assert Decimal(str(dash['lifetime_earnings'])) == Decimal('13.88')
    assert Decimal(str(dash['account_balance'])) == Decimal('13.88')

    order.items[0].final_weight = Decimal('10.000')
    sync_order_pricing(order, reprice_lines=False)
    db_session.flush()
    db_session.refresh(entry)
    db_session.refresh(inf)
    assert Decimal(str(entry.amount)) == Decimal('15.00')
    assert Decimal(str(inf.store_credit_balance)) == Decimal('15.00')
    dash = influencer_service.dashboard_for(inf.id)
    assert Decimal(str(dash['lifetime_earnings'])) == Decimal('15.00')
    assert Decimal(str(dash['account_balance'])) == Decimal('15.00')

    detail = influencer_service.customer_detail_for(inf.id, customer.id)
    item = detail['orders'][0]['items'][0]
    assert item['commission_estimated'] is False
    assert Decimal(str(item['commission_amount'])) == Decimal('15.00')
    assert item['weight_estimated'] is False
    assert Decimal(str(item['weight'])) == Decimal('10')


def test_no_self_commission(app, db_session):
    inf = _make_influencer(phone='+10000000020')
    inf.referred_by_user_id = inf.id
    product = _product('猪')
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('3'),
    ))
    db_session.flush()
    order = _order(inf, _deal(), product)
    mark_order_paid(order)
    db_session.flush()
    assert InfluencerCommissionEntry.query.filter_by(order_id=order.id).first() is None


def test_reverse_on_unpaid(app, db_session):
    inf = _make_influencer(phone='+10000000021')
    customer = _user('+10000000022', 'C8')
    customer.referred_by_user_id = inf.id
    product = _product('牛')
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('4'),
    ))
    db_session.flush()
    order = _order(customer, _deal(), product, qty=1)
    mark_order_paid(order)
    db_session.flush()
    assert Decimal(str(inf.store_credit_balance)) == Decimal('4')
    influencer_service.reverse_for_order(order)
    db_session.flush()
    entry = InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()
    assert entry.status == STATUS_REVERSED
    assert Decimal(str(inf.store_credit_balance)) == Decimal('0')


def test_influencer_api_rbac_and_no_phone(app, db_session):
    inf = _make_influencer(phone='+10000000023')
    regular = _user('+10000000024', 'Norm')
    customer = _user('+10000000025', 'Lead', wechat='abcdefghi')
    customer.referred_by_user_id = inf.id
    db_session.flush()
    client = app.test_client()

    res = client.get('/api/influencer/customers', headers={'Authorization': f'Bearer {_token(regular)}'})
    assert res.status_code == 403

    res = client.get('/api/influencer/customers', headers={'Authorization': f'Bearer {_token(inf)}'})
    assert res.status_code == 200
    rows = res.get_json()['customers']
    assert len(rows) == 1
    assert 'phone' not in rows[0]
    assert rows[0]['wechat_masked'] == 'ab***hi'
    assert rows[0]['nickname']

    detail = client.get(
        f'/api/influencer/customers/{customer.id}',
        headers={'Authorization': f'Bearer {_token(inf)}'},
    )
    assert detail.status_code == 200
    body = detail.get_json()
    assert 'phone' not in body['customer']
    assert 'address' not in str(body)


def test_customer_list_splits_in_progress_and_closed_orders(app, db_session):
    inf = _make_influencer(phone='+10000000040')
    customer = _user('+10000000041', 'Lead')
    customer.referred_by_user_id = inf.id
    product = _product()
    open_deal = _deal()
    closed_deal = GroupDeal(
        title='Past',
        order_start_date=datetime(2025, 1, 1),
        order_end_date=datetime(2025, 1, 10),
        pickup_date=datetime(2025, 1, 15),
        status='completed',
    )
    db_session.add(closed_deal)
    db_session.flush()
    open_order = _order(customer, open_deal, product, qty=1)
    closed_order = _order(customer, closed_deal, product, qty=3)
    closed_order.status = OrderStatus.COMPLETED.value
    closed_order.payment_status = PaymentStatus.PAID.value
    cancelled = _order(customer, open_deal, product, qty=4)
    cancelled.status = OrderStatus.CANCELLED.value
    db_session.flush()

    rows = influencer_service.customers_for(inf.id)
    assert len(rows) == 1
    assert rows[0]['in_progress_order_count'] == 1
    assert rows[0]['closed_order_count'] == 1
    assert rows[0]['order_count'] == 2

    detail = influencer_service.customer_detail_for(inf.id, customer.id)
    phases = {row['id']: row['phase'] for row in detail['orders']}
    assert phases[open_order.id] == 'in_progress'
    assert phases[closed_order.id] == 'closed'
    assert cancelled.id not in phases
    open_row = next(row for row in detail['orders'] if row['id'] == open_order.id)
    assert open_row['items'][0]['product_name'] == '鸭'
    assert open_row['items'][0]['commission_type'] == 'per_item'
    assert open_row['items'][0]['commission_unit'] == '件'
    assert open_row['items'][0]['price_unit'] == '件'


def test_customer_list_sorts_active_then_closed_then_none(app, db_session):
    inf = _make_influencer(phone='+10000000060')
    product = _product('排骨')
    open_deal = _deal()
    closed_deal = GroupDeal(
        title='Past',
        order_start_date=datetime(2025, 1, 1),
        order_end_date=datetime(2025, 1, 10),
        pickup_date=datetime(2025, 1, 15),
        status='completed',
    )
    db_session.add(closed_deal)
    db_session.flush()
    none = _user('+10000000061', 'None')
    hist_few = _user('+10000000062', 'Hist1')
    hist_many = _user('+10000000063', 'Hist2')
    active = _user('+10000000064', 'Active')
    for u in (none, hist_few, hist_many, active):
        u.referred_by_user_id = inf.id
    db_session.flush()
    _order(hist_few, closed_deal, product, qty=1)
    _order(hist_many, closed_deal, product, qty=1)
    _order(hist_many, closed_deal, product, qty=2)
    _order(active, open_deal, product, qty=1)
    db_session.flush()

    names = [row['nickname'] for row in influencer_service.customers_for(inf.id)]
    assert names == ['Active', 'Hist2', 'Hist1', 'None']


def test_customer_detail_estimates_weight_commission_with_min_weight(app, db_session):
    inf = _make_influencer(phone='+10000000050')
    customer = _user('+10000000051', 'Lead')
    customer.referred_by_user_id = inf.id
    product = Product(
        name='羊腿',
        pricing_type='bundled_weight',
        pricing_data={'price_per_unit': 5, 'unit': 'lb', 'min_weight': 7, 'max_weight': 15},
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    db_session.add(InfluencerProductRate(
        product_id=product.id,
        commission_type='per_weight',
        amount=Decimal('1.50'),
    ))
    db_session.flush()
    order = _order(customer, _deal(), product, qty=2, unit=Decimal('5.00'))
    db_session.flush()

    detail = influencer_service.customer_detail_for(inf.id, customer.id)
    item = detail['orders'][0]['items'][0]
    assert item['commission_type'] == 'per_weight'
    assert item['commission_unit'] == 'lb'
    assert item['price_unit'] == 'lb'
    assert item['weight_estimated'] is True
    assert Decimal(str(item['weight'])) == Decimal('14')
    assert Decimal(str(item['commission_rate'])) == Decimal('1.50')
    assert Decimal(str(item['commission_amount'])) == Decimal('21.00')
    assert item['commission_estimated'] is True

    order.items[0].final_weight = Decimal('9.250')
    db_session.flush()
    weighed = influencer_service.customer_detail_for(inf.id, customer.id)['orders'][0]['items'][0]
    assert weighed['weight_estimated'] is False
    assert Decimal(str(weighed['weight'])) == Decimal('9.250')
    assert Decimal(str(weighed['commission_amount'])) == Decimal('13.88')
    assert weighed['commission_estimated'] is False


def test_assign_persists_global_rates_and_keeps_admin_edits(app, db_session):
    sdr = SDR(name='Partner', source_identifier='partner', is_active=True)
    db_session.add(sdr)
    db_session.flush()
    duck = _product('水鸭', price=30)
    extra = _product('其它', price=10)
    db_session.add(CommissionRule(
        sdr_id=sdr.id,
        product_id=duck.id,
        commission_type='per_item',
        own_customer_amount=Decimal('6.00'),
        general_customer_amount=Decimal('1.50'),
        is_active=True,
    ))
    db_session.flush()

    _make_influencer(phone='+10000000028')
    duck_rate = InfluencerProductRate.query.filter_by(product_id=duck.id).first()
    extra_rate = InfluencerProductRate.query.filter_by(product_id=extra.id).first()
    assert duck_rate is not None
    assert extra_rate is not None
    assert Decimal(str(duck_rate.amount)) == Decimal('1.50')
    assert Decimal(str(extra_rate.amount)) == Decimal('0')

    duck_rate.amount = Decimal('9.00')
    db_session.flush()
    _make_influencer(phone='+10000000029', nickname='后任')
    assert Decimal(str(InfluencerProductRate.query.filter_by(product_id=duck.id).first().amount)) == Decimal('9.00')
    assert InfluencerProductRate.query.count() == 2


def test_convert_source_customers_stops_sdr_and_skips_other_login(app, db_session):
    sdr = SDR(name='Partner', source_identifier='partner', is_active=True)
    db_session.add(sdr)
    db_session.flush()
    owner = _user('+15196140000', 'OwnerPhone', user_source='partner')
    other_login = User(
        phone=None,
        nickname='OwnerGoogle',
        email='owner@example.com',
        user_source='partner',
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(other_login)
    customer = _user('+15196140001', 'Cust', user_source='partner')
    outsider = _user('+15196140002', 'Other', user_source='default')
    record = CommissionRecord(
        group_deal_id=_deal().id,
        sdr_id=sdr.id,
        total_commission=Decimal('10.00'),
        own_customer_commission=Decimal('10.00'),
        general_customer_commission=Decimal('0'),
        payment_status='pending',
    )
    db_session.add(record)
    db_session.flush()
    record_id = record.id

    result = influencer_service.convert_source_customers_to_influencer(
        owner.id, 'partner', exclude_user_ids=[other_login.id]
    )
    db_session.flush()

    db_session.refresh(owner)
    assert owner.is_influencer is True
    assert customer.referred_by_user_id == owner.id
    assert other_login.referred_by_user_id is None
    assert outsider.referred_by_user_id is None
    assert SDR.query.get(sdr.id).is_active is False
    assert result['bound_count'] == 1
    assert Decimal(str(CommissionRecord.query.get(record_id).total_commission)) == Decimal('10.00')


def test_influencer_self_buy_shows_and_charges_price_minus_commission(app, db_session):
    from utils.influencer_pricing import apply_influencer_discount_to_product_payload
    from utils.order_item_pricing import priced_items_from_request

    inf = _make_influencer(phone='+10000000070')
    regular = _user('+10000000071', 'Norm')
    product = _product('鸡蛋', price=16)
    db_session.add(InfluencerProductRate(
        product_id=product.id, commission_type='per_item', amount=Decimal('0.25'),
    ))
    deal = _deal()
    db_session.add(GroupDealProduct(group_deal_id=deal.id, product_id=product.id, is_discount=False))
    db_session.flush()

    payload = deal_product_to_dict(
        GroupDealProduct.query.filter_by(group_deal_id=deal.id, product_id=product.id).first(),
        product=product,
    )
    discounted = apply_influencer_discount_to_product_payload(dict(payload), inf.id)
    assert discounted['influencer_discount'] is True
    assert Decimal(str(discounted['display_price'])) == Decimal('15.75')
    assert Decimal(str(discounted['original_price'])) == Decimal('16.00')
    unchanged = apply_influencer_discount_to_product_payload(dict(payload), regular.id)
    assert not unchanged.get('influencer_discount')

    items, subtotal = priced_items_from_request(
        [{'product_id': product.id, 'quantity': 2}],
        group_deal_id=deal.id,
        buyer_user_id=inf.id,
    )
    assert Decimal(str(items[0]['unit_price'])) == Decimal('15.75')
    assert Decimal(str(subtotal)) == Decimal('31.50')

    items2, subtotal2 = priced_items_from_request(
        [{'product_id': product.id, 'quantity': 2}],
        group_deal_id=deal.id,
        buyer_user_id=regular.id,
    )
    assert Decimal(str(items2[0]['unit_price'])) == Decimal('16.00')
    assert Decimal(str(subtotal2)) == Decimal('32.00')
