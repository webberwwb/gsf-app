"""Order lines keep the price from when they were placed."""
from datetime import datetime, timedelta
from decimal import Decimal

from constants.status_enums import UserStatus
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem
from models.product import Product
from models.product_variant import ProductVariant
from models.user import User
from utils.order_item_pricing import (
    backfill_pricing_snapshots,
    build_priced_order_item,
    clear_locked_price_choices_matching_catalog,
    enrich_order_item_dict,
    price_from_snapshot,
    recalculate_existing_item,
)
from utils.order_lock import order_money_locked
from utils.order_totals import sync_order_pricing
from utils.product_price_choices import (
    apply_deal_sale_to_open_orders,
    apply_order_price_choices,
    open_order_price_impact,
    price_choice_rejection,
)


def _user(db_session, phone, name='Buyer'):
    user = User(phone=phone, nickname=name, status=UserStatus.ACTIVE.value)
    db_session.add(user)
    db_session.flush()
    return user


def _deal(db_session, status='active', end=None):
    deal = GroupDeal(
        title='Open Deal',
        order_start_date=datetime(2026, 1, 1),
        order_end_date=end or datetime(2026, 12, 31),
        pickup_date=datetime(2026, 6, 1),
        status=status,
    )
    db_session.add(deal)
    db_session.flush()
    return deal


def _product(db_session, price=10, breaks=None):
    data = {'price': price}
    if breaks:
        data['quantity_breaks'] = breaks
    product = Product(name='Apple', pricing_type='per_item', pricing_data=data, is_active=True)
    db_session.add(product)
    db_session.flush()
    return product


def _order(db_session, user, deal, product, qty=1, status='submitted', payment='unpaid', weight=None, variant_id=None):
    priced = build_priced_order_item(
        product,
        quantity=qty,
        final_weight=weight,
        variant_id=variant_id,
        require_variant=bool(variant_id),
    )
    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        order_number=f'TEST-SNAP-{user.id}-{product.id}-{qty}-{status}-{payment}',
        subtotal=Decimal(str(priced['total_price'])),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal(str(priced['total_price'])),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method='pickup',
        payment_method='cash',
        payment_status=payment,
        status=status,
        store_credit_applied=Decimal('0'),
    )
    db_session.add(order)
    db_session.flush()
    db_session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=qty,
        unit_price=Decimal(str(priced['unit_price'])),
        total_price=Decimal(str(priced['total_price'])),
        final_weight=weight,
        variant_id=priced['variant_id'],
        variant_name=priced['variant_name'],
        pricing_snapshot=priced['pricing_snapshot'],
    ))
    db_session.flush()
    return order


def test_snapshot_replay_matches_catalog_price_at_order_time():
    product = Product(name='Pear', pricing_type='per_item', pricing_data={
        'price': 10,
        'quantity_breaks': [{'min_qty': 3, 'price': 8}],
    }, is_active=True)
    priced = build_priced_order_item(product, quantity=3, product_qty=3)
    unit, total, _fee = price_from_snapshot(
        priced['pricing_snapshot'], 3, product_qty=3
    )
    assert priced['unit_price'] == 8
    assert unit == 8
    assert total == 24


def test_catalog_change_does_not_reprice_existing_line(app, db_session):
    user = _user(db_session, '9991110001')
    deal = _deal(db_session)
    product = _product(db_session, price=10, breaks=[{'min_qty': 3, 'price': 8}])
    order = _order(db_session, user, deal, product, qty=3)
    item = order.items[0]
    product.pricing_data = {'price': 20, 'quantity_breaks': [{'min_qty': 3, 'price': 15}]}
    recalculate_existing_item(item, product, product_qty=3)
    assert float(item.unit_price) == 8
    assert float(item.total_price) == 24


def test_weight_uses_snapshotted_rate(app, db_session):
    user = _user(db_session, '9991110002')
    deal = _deal(db_session)
    product = Product(
        name='Fish',
        pricing_type='unit_weight',
        pricing_data={'price_per_unit': 5, 'unit': 'lb'},
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    priced = build_priced_order_item(product, quantity=1, final_weight=2)
    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        order_number='TEST-SNAP-WT',
        subtotal=Decimal(str(priced['total_price'])),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal(str(priced['total_price'])),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method='pickup',
        payment_method='cash',
        payment_status='unpaid',
        status='preparing',
        store_credit_applied=Decimal('0'),
    )
    db_session.add(order)
    db_session.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal(str(priced['unit_price'])),
        total_price=Decimal(str(priced['total_price'])),
        final_weight=Decimal('2'),
        pricing_snapshot=priced['pricing_snapshot'],
    )
    db_session.add(item)
    db_session.flush()
    product.pricing_data = {'price_per_unit': 9, 'unit': 'lb'}
    item.final_weight = Decimal('4')
    recalculate_existing_item(item, product)
    assert float(item.unit_price) == 5
    assert float(item.total_price) == 20


def test_paid_order_sync_keeps_totals(app, db_session):
    user = _user(db_session, '9991110003')
    deal = _deal(db_session)
    product = _product(db_session, price=12)
    order = _order(db_session, user, deal, product, payment='paid', status='completed')
    assert order_money_locked(order)
    product.pricing_data = {'price': 40}
    sync_order_pricing(order)
    item = order.items[0]
    assert float(item.total_price) == 12
    assert float(order.total) == 12


def test_price_choice_old_and_new_and_closed_deal(app, db_session):
    user = _user(db_session, '9991110004')
    open_deal = _deal(db_session, status='active')
    closed_deal = _deal(db_session, status='closed', end=datetime(2026, 1, 2))
    closed_deal.title = 'Closed Deal'
    product = _product(db_session, price=10)
    open_order = _order(db_session, user, open_deal, product, qty=1)
    closed_user = _user(db_session, '9991110005', 'Other')
    closed_order = _order(db_session, closed_user, closed_deal, product, qty=2)
    proposal = {'pricing_type': 'per_item', 'pricing_data': {'price': 14}}
    impact = open_order_price_impact(product, proposal)
    ids = {row['order_id'] for row in impact['orders']}
    assert open_order.id in ids
    assert closed_order.id not in ids
    assert price_choice_rejection(impact, None)['code'] == 'price_choice_required'
    assert price_choice_rejection(impact, [{'order_id': open_order.id, 'choice': 'old'}]) is None

    apply_order_price_choices(product, impact, [{'order_id': open_order.id, 'choice': 'old'}])
    item = open_order.items[0]
    assert item.price_choice == 'locked_old'
    assert float(item.total_price) == 10

    product.pricing_data = {'price': 14}
    same = open_order_price_impact(product, {'pricing_type': 'per_item', 'pricing_data': {'price': 14}})
    assert same['orders'] == []
    apply_order_price_choices(
        product, impact, [{'order_id': open_order.id, 'choice': 'new'}]
    )
    assert item.price_choice == 'applied_new'
    assert float(item.unit_price) == 14
    assert float(item.total_price) == 14
    assert float(closed_order.items[0].total_price) == 20


def test_price_choice_hidden_when_charged_total_stays_the_same(app, db_session):
    user = _user(db_session, '9991110030')
    deal = _deal(db_session)
    product = _product(db_session, price=29)
    order = _order(db_session, user, deal, product, qty=1)
    item = order.items[0]
    item.unit_price = Decimal('32')
    item.total_price = Decimal('32')
    order.subtotal = Decimal('32')
    order.total = Decimal('32')
    db_session.flush()

    impact = open_order_price_impact(product, {
        'pricing_type': 'per_item',
        'pricing_data': {'price': 32},
    })
    assert impact['orders'] == []

    changed = open_order_price_impact(product, {
        'pricing_type': 'per_item',
        'pricing_data': {'price': 34},
    })
    assert order.id in _ids(changed)
    assert changed['orders'][0]['old_total'] == 32
    assert changed['orders'][0]['new_total'] == 34


def test_locked_old_clears_when_catalog_price_matches_the_line(app, db_session):
    user = _user(db_session, '9991110031')
    deal = _deal(db_session)
    product = _product(db_session, price=32)
    order = _order(db_session, user, deal, product, qty=1)
    item = order.items[0]
    item.price_choice = 'locked_old'
    db_session.flush()

    matched = enrich_order_item_dict(item, product)
    assert matched['price_choice'] is None
    assert 'catalog_total_price' not in matched
    assert item.price_choice is None

    product.pricing_data = {'price': 40}
    item.price_choice = 'locked_old'
    db_session.flush()
    moved = enrich_order_item_dict(item, product)
    assert moved['price_choice'] == 'locked_old'
    assert moved['catalog_total_price'] == 40

    product.pricing_data = {'price': 32}
    clear_locked_price_choices_matching_catalog(product)
    assert item.price_choice is None


def test_backfill_keeps_stored_price_when_catalog_moved(app, db_session):
    user = _user(db_session, '9991110006')
    deal = _deal(db_session)
    product = _product(db_session, price=30)
    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        order_number='TEST-SNAP-BF',
        subtotal=Decimal('10'),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal('10'),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method='pickup',
        payment_method='cash',
        payment_status='unpaid',
        status='submitted',
        store_credit_applied=Decimal('0'),
    )
    db_session.add(order)
    db_session.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal('10'),
        total_price=Decimal('10'),
    )
    db_session.add(item)
    db_session.flush()
    backfill_pricing_snapshots()
    assert item.pricing_snapshot['synthetic'] is True
    assert float(item.unit_price) == 10
    product.pricing_data = {'price': 99}
    recalculate_existing_item(item, product)
    assert float(item.total_price) == 10


def test_backfill_keeps_breaks_when_catalog_still_matches(app, db_session):
    user = _user(db_session, '9991110007')
    deal = _deal(db_session)
    product = _product(db_session, price=10, breaks=[{'min_qty': 3, 'price': 8}])
    order = _order(db_session, user, deal, product, qty=3)
    item = order.items[0]
    item.pricing_snapshot = None
    db_session.flush()
    backfill_pricing_snapshots()
    assert item.pricing_snapshot['synthetic'] is False
    assert item.pricing_snapshot['pricing_data']['quantity_breaks'][0]['price'] == 8
    assert float(item.total_price) == 24


def _on_sale(db_session, deal, product):
    db_session.add(GroupDealProduct(
        group_deal_id=deal.id,
        product_id=product.id,
        is_discount=True,
    ))
    db_session.flush()


def _ids(impact):
    return {row['order_id'] for row in impact['orders']}


def test_sale_price_does_not_ask_for_a_choice_but_list_price_does(app, db_session):
    user = _user(db_session, '9991110010')
    deal = _deal(db_session)
    product = _product(db_session, price=10)
    _on_sale(db_session, deal, product)
    order = _order(db_session, user, deal, product, qty=1)
    sale_only = {'pricing_type': 'per_item', 'pricing_data': {'price': 10, 'sale_price': 8}}
    assert open_order_price_impact(product, sale_only)['orders'] == []
    assert sale_only['pricing_data']['sale_price'] == 8

    impact = open_order_price_impact(product, {
        'pricing_type': 'per_item',
        'pricing_data': {'price': 14, 'sale_price': 8},
    })
    assert order.id in _ids(impact)
    row = impact['orders'][0]
    assert row['old_total'] == 10
    assert row['new_total'] == 14

    product.pricing_data = {'price': 14, 'sale_price': 8}
    apply_order_price_choices(product, impact, [{'order_id': order.id, 'choice': 'new'}])
    assert float(order.items[0].total_price) == 14


def test_variant_sale_price_does_not_ask_and_variant_list_price_does(app, db_session):
    user = _user(db_session, '9991110011')
    deal = _deal(db_session)
    product = Product(
        name='Apple',
        pricing_type='per_item',
        pricing_data={'price': 10},
        variants_share_price=False,
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    variant = ProductVariant(product_id=product.id, name='大', price=Decimal('12'), price_delta=Decimal('0'))
    db_session.add(variant)
    db_session.flush()
    db_session.refresh(product)
    _on_sale(db_session, deal, product)
    order = _order(db_session, user, deal, product, variant_id=variant.id)
    assert float(order.items[0].total_price) == 12

    same_list = {
        'pricing_type': 'per_item',
        'pricing_data': {'price': 10},
        'variants_share_price': False,
        'variants': [{'id': variant.id, 'name': '大', 'price': 12, 'sale_price': 9, 'price_delta': 0}],
    }
    assert open_order_price_impact(product, same_list)['orders'] == []

    impact = open_order_price_impact(product, {
        'pricing_type': 'per_item',
        'pricing_data': {'price': 10},
        'variants_share_price': False,
        'variants': [{'id': variant.id, 'name': '大', 'price': 15, 'sale_price': 9, 'price_delta': 0}],
    })
    assert order.id in _ids(impact)
    assert impact['orders'][0]['new_total'] == 15


def test_unit_and_bundle_sale_rates_do_not_ask(app, db_session):
    user = _user(db_session, '9991110012')
    deal = _deal(db_session)
    unit = Product(
        name='By pound',
        pricing_type='unit_weight',
        pricing_data={'price_per_unit': 5},
        is_active=True,
    )
    bundled = Product(
        name='Bundle',
        pricing_type='bundled_weight',
        pricing_data={'price_per_unit': 5, 'min_weight': 2, 'max_weight': 4},
        is_active=True,
    )
    db_session.add_all([unit, bundled])
    db_session.flush()
    _on_sale(db_session, deal, unit)
    _on_sale(db_session, deal, bundled)
    unit_order = _order(db_session, user, deal, unit, weight=2)
    other = _user(db_session, '9991110013')
    bundle_order = _order(db_session, other, deal, bundled, weight=2)
    assert float(unit_order.items[0].total_price) == 10
    assert float(bundle_order.items[0].total_price) == 10

    assert open_order_price_impact(unit, {
        'pricing_type': 'unit_weight',
        'pricing_data': {'price_per_unit': 5, 'sale_price_per_unit': 4},
    })['orders'] == []
    assert open_order_price_impact(bundled, {
        'pricing_type': 'bundled_weight',
        'pricing_data': {'price_per_unit': 5, 'min_weight': 2, 'max_weight': 4, 'sale_price_per_unit': 4},
    })['orders'] == []

    unit_impact = open_order_price_impact(unit, {
        'pricing_type': 'unit_weight',
        'pricing_data': {'price_per_unit': 6, 'sale_price_per_unit': 4},
    })
    assert unit_order.id in _ids(unit_impact)
    assert unit_impact['orders'][0]['new_total'] == 12

    bundle_impact = open_order_price_impact(bundled, {
        'pricing_type': 'bundled_weight',
        'pricing_data': {'price_per_unit': 6, 'min_weight': 2, 'max_weight': 4, 'sale_price_per_unit': 4},
    })
    assert bundle_order.id in _ids(bundle_impact)
    assert bundle_impact['orders'][0]['new_total'] == 12


def test_weight_range_sale_amount_does_not_ask_and_band_price_does(app, db_session):
    user = _user(db_session, '9991110014')
    deal = _deal(db_session)
    ranges = [
        {'min_weight': 3, 'max_weight': 3.5, 'price': 29},
        {'min_weight': 3.5, 'max_weight': 4, 'price': 30},
    ]
    product = Product(
        name='珍珠鸡',
        pricing_type='weight_range',
        pricing_data={'ranges': ranges},
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    _on_sale(db_session, deal, product)
    order = _order(db_session, user, deal, product, weight=3.2)
    assert float(order.items[0].total_price) == 29

    assert open_order_price_impact(product, {
        'pricing_type': 'weight_range',
        'pricing_data': {'ranges': ranges, 'sale_amount_off': 2},
    })['orders'] == []

    new_ranges = [
        {'min_weight': 3, 'max_weight': 3.5, 'price': 31},
        {'min_weight': 3.5, 'max_weight': 4, 'price': 30},
    ]
    impact = open_order_price_impact(product, {
        'pricing_type': 'weight_range',
        'pricing_data': {'ranges': new_ranges, 'sale_amount_off': 2},
    })
    assert order.id in _ids(impact)
    assert impact['orders'][0]['old_total'] == 29
    assert impact['orders'][0]['new_total'] == 31

    product.pricing_data = {'ranges': new_ranges, 'sale_amount_off': 2}
    apply_order_price_choices(product, impact, [{'order_id': order.id, 'choice': 'new'}])
    assert float(order.items[0].total_price) == 31


def test_quantity_break_change_still_asks(app, db_session):
    user = _user(db_session, '9991110015')
    deal = _deal(db_session)
    product = _product(db_session, price=10)
    order = _order(db_session, user, deal, product, qty=3)
    impact = open_order_price_impact(product, {
        'pricing_type': 'per_item',
        'pricing_data': {'price': 10, 'quantity_breaks': [{'min_qty': 3, 'price': 7}], 'sale_price': 6},
    })
    assert order.id in _ids(impact)
    assert impact['orders'][0]['old_total'] == 30
    assert impact['orders'][0]['new_total'] == 21


def test_turning_on_deal_discount_reprices_open_orders_without_asking(app, db_session):
    buyer = _user(db_session, '9991110020')
    other_buyer = _user(db_session, '9991110021')
    paid_buyer = _user(db_session, '9991110022')
    deal = _deal(db_session)
    other_deal = _deal(db_session)
    ranges = [
        {'min_weight': 3, 'max_weight': 3.5, 'price': 29},
        {'min_weight': 3.5, 'max_weight': 4, 'price': 30},
    ]
    chicken = Product(
        name='珍珠鸡',
        pricing_type='weight_range',
        pricing_data={'ranges': ranges, 'sale_amount_off': 2},
        is_active=True,
    )
    apple = _product(db_session, price=10)
    apple.pricing_data = {'price': 10, 'sale_price': 8}
    db_session.add(chicken)
    db_session.flush()
    for group, product in ((deal, chicken), (deal, apple), (other_deal, chicken)):
        db_session.add(GroupDealProduct(
            group_deal_id=group.id,
            product_id=product.id,
            is_discount=False,
        ))
    db_session.flush()

    open_chicken = _order(db_session, buyer, deal, chicken, weight=3.2)
    open_apple = _order(db_session, buyer, deal, apple)
    other = _order(db_session, other_buyer, other_deal, chicken, weight=3.2)
    paid = _order(db_session, paid_buyer, deal, chicken, weight=3.2, payment='paid')
    assert float(open_chicken.items[0].total_price) == 29
    assert float(open_apple.items[0].total_price) == 10

    for link in GroupDealProduct.query.filter_by(group_deal_id=deal.id).all():
        link.is_discount = True
    db_session.flush()
    apply_deal_sale_to_open_orders(deal, [chicken.id, apple.id])

    assert float(open_chicken.items[0].total_price) == 27
    assert open_chicken.items[0].price_choice is None
    assert float(open_apple.items[0].total_price) == 8
    assert float(other.items[0].total_price) == 29
    assert float(paid.items[0].total_price) == 29
    assert float(open_chicken.total) == 27

    for link in GroupDealProduct.query.filter_by(group_deal_id=deal.id).all():
        link.is_discount = False
    db_session.flush()
    apply_deal_sale_to_open_orders(deal, [chicken.id, apple.id])
    assert float(open_chicken.items[0].total_price) == 29
    assert float(open_apple.items[0].total_price) == 10
    assert float(other.items[0].total_price) == 29


def test_closed_deal_discount_does_not_reprice(app, db_session):
    user = _user(db_session, '9991110023')
    deal = _deal(db_session, status='closed')
    product = _product(db_session, price=10)
    product.pricing_data = {'price': 10, 'sale_price': 8}
    db_session.add(GroupDealProduct(
        group_deal_id=deal.id, product_id=product.id, is_discount=True,
    ))
    db_session.flush()
    order = _order(db_session, user, deal, product)
    apply_deal_sale_to_open_orders(deal, [product.id])
    assert float(order.items[0].total_price) == 10
