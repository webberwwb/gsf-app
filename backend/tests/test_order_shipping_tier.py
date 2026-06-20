"""Shipping tier base and eligible subtotal (mirrors shared/order-pricing/shipping.js)."""
from decimal import Decimal

from utils.shipping import (
    adjustment_discount,
    eligible_tier_subtotal_from_items,
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
