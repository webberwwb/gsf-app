"""Shipping tier base and eligible subtotal (mirrors shared/order-pricing/shipping.js)."""
from decimal import Decimal

from utils.shipping import (
    adjustment_discount,
    calculate_shipping_fee,
    eligible_tier_subtotal_from_items,
    match_region_surcharge,
    region_surcharge_for_address,
    shipping_tier_base_from_parts,
    get_shipping_fee_for_subtotal,
)


class FakeProduct:
    def __init__(self, counts_toward_free_shipping=True):
        self.counts_toward_free_shipping = counts_toward_free_shipping


def test_adjustment_discount_only_negative():
    assert adjustment_discount(10) == Decimal('0')
    assert adjustment_discount(-10) == Decimal('-10')


def test_shipping_tier_base_credit_and_discount():
    base = shipping_tier_base_from_parts(100, credit=20, adjustment=-10)
    assert base == Decimal('70.00')


def test_shipping_tier_base_excludes_cutting_fees():
    base = shipping_tier_base_from_parts(151, credit=0, adjustment=0, cutting_fees=3)
    assert base == Decimal('148.00')


def test_shipping_tier_base_ignores_penalty():
    base = shipping_tier_base_from_parts(100, credit=0, adjustment=15)
    assert base == Decimal('100.00')


def test_eligible_tier_proportional_exclusion():
    items = [
        {'product': FakeProduct(True), 'total_price': 60},
        {'product': FakeProduct(False), 'total_price': 40},
    ]
    tier = eligible_tier_subtotal_from_items(items, Decimal('80'))
    assert tier == Decimal('48.00')


def test_shipping_fee_from_tier_subtotal():
    config = type('Cfg', (), {
        'tiers': [
            {'threshold': 0, 'fee': 7.99},
            {'threshold': 150, 'fee': 0},
        ]
    })()
    fee = get_shipping_fee_for_subtotal(Decimal('160'), config=config)
    assert fee == Decimal('0.00')


class RegionCfg:
    def __init__(self):
        self.tiers = [
            {'threshold': 0, 'fee': 7.99},
            {'threshold': 150, 'fee': 0},
        ]
        self.region_surcharges = None
        self.distance_surcharges = None


def test_region_surcharge_defaults():
    cfg = RegionCfg()
    assert match_region_surcharge(cfg, {'city': 'Waterloo'})['surcharge'] == Decimal('4.00')
    assert match_region_surcharge(cfg, {'city': 'Kitchener'})['surcharge'] == Decimal('4.00')
    assert match_region_surcharge(cfg, {'city': 'Guelph'})['surcharge'] == Decimal('4.00')
    assert match_region_surcharge(cfg, {'city': 'Whitby'})['surcharge'] == Decimal('2.00')
    assert match_region_surcharge(cfg, {'city': 'Pickering'})['surcharge'] == Decimal('2.00')
    assert match_region_surcharge(cfg, {'city': 'Ajax'})['surcharge'] == Decimal('2.00')
    assert match_region_surcharge(cfg, {'city': 'Hamilton'})['surcharge'] == Decimal('2.00')
    assert match_region_surcharge(cfg, {'city': 'Burlington'})['surcharge'] == Decimal('2.00')
    assert match_region_surcharge(cfg, {'city': 'Markham'})['surcharge'] == Decimal('0.00')
    assert match_region_surcharge(cfg, {'city': 'Toronto'})['surcharge'] == Decimal('0.00')
    assert region_surcharge_for_address(cfg, None) == Decimal('0.00')


def test_old_km_rings_are_ignored():
    cfg = RegionCfg()
    cfg.distance_surcharges = [{'max_km': 10, 'surcharge': 99, 'label': 'near'}]
    assert region_surcharge_for_address(cfg, {'city': 'Waterloo'}) == Decimal('4.00')
    assert region_surcharge_for_address(cfg, {'city': 'Markham'}) == Decimal('0.00')


def test_calculate_shipping_fee_adds_region_surcharge():
    cfg = RegionCfg()
    fee = calculate_shipping_fee(
        Decimal('40'),
        'delivery',
        address={'city': 'Waterloo'},
        config=cfg,
    )
    assert fee == Decimal('11.99')


def test_free_shipping_keeps_region_delta():
    cfg = RegionCfg()
    whitby = calculate_shipping_fee(
        Decimal('160'),
        'delivery',
        address={'city': 'Whitby'},
        config=cfg,
    )
    waterloo = calculate_shipping_fee(
        Decimal('160'),
        'delivery',
        address={'city': 'Waterloo'},
        config=cfg,
    )
    markham = calculate_shipping_fee(
        Decimal('160'),
        'delivery',
        address={'city': 'Markham'},
        config=cfg,
    )
    assert whitby == Decimal('2.00')
    assert waterloo == Decimal('4.00')
    assert markham == Decimal('0.00')


def test_calculate_shipping_fee_pickup_ignores_region():
    cfg = RegionCfg()
    fee = calculate_shipping_fee(
        Decimal('40'),
        'pickup',
        address={'city': 'Waterloo'},
        config=cfg,
    )
    assert fee == Decimal('0.00')
