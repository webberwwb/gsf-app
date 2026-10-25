"""Weight-range sale_amount_off: one amount off every band, only for 本团折扣."""
from decimal import Decimal

import pytest
from marshmallow import ValidationError

from schemas.product import validate_pricing_config
from utils.order_item_pricing import (
    build_pricing_snapshot,
    compute_base_price,
    price_from_snapshot,
)
from utils.order_points import calculate_order_points


BANDS = [
    {'min': 3, 'max': 3.5, 'price': 29},
    {'min': 3.5, 'max': 4, 'price': 30},
    {'min': 4, 'max': 4.5, 'price': 31},
    {'min': 4.5, 'max': 5, 'price': 32},
    {'min': 5, 'max': None, 'price': 33},
]


class _Product:
    def __init__(self, on_sale=True):
        self.pricing_type = 'weight_range'
        self.pricing_data = {
            'sale_amount_off': 2,
            'ranges': [dict(row) for row in BANDS],
        }
        self.is_discount = on_sale
        self.variants_share_price = True
        self.substitute_enabled = False
        self.counts_toward_free_shipping = True


class _Order:
    def __init__(self, subtotal):
        self.subtotal = Decimal(str(subtotal))
        self.store_credit_applied = Decimal('0')
        self.shipping_fee = Decimal('0')
        self.adjustment_amount = Decimal('0')
        self.items = []


def test_on_sale_band_is_reduced_by_the_same_amount():
    product = _Product(on_sale=True)
    unit, total = compute_base_price(product, 1, final_weight=3.2)
    assert unit == 27
    assert total == 27
    assert product.pricing_data['ranges'][0]['price'] == 29
    assert product.pricing_data['ranges'][1]['price'] == 30


def test_list_band_when_deal_is_not_on_sale():
    product = _Product(on_sale=False)
    unit, total = compute_base_price(product, 1, final_weight=3.2)
    assert unit == 29
    assert total == 29


def test_snapshot_replay_does_not_subtract_twice():
    product = _Product(on_sale=True)
    snap = build_pricing_snapshot(product)
    assert snap['pricing_data']['ranges'][0]['price'] == 27
    assert snap['pricing_data']['ranges'][-1]['price'] == 31
    unit, total, _fee = price_from_snapshot(snap, 1, final_weight=3.2)
    assert unit == 27
    assert total == 27


def test_points_use_the_reduced_band():
    product = _Product(on_sale=True)
    _unit, total = compute_base_price(product, 1, final_weight=3.2)
    assert calculate_order_points(_Order(total)) == 2700


def test_sale_amount_off_must_stay_below_the_cheapest_band():
    ok = {'ranges': [dict(row) for row in BANDS], 'sale_amount_off': 2}
    validate_pricing_config('weight_range', ok)
    too_high = {'ranges': [dict(row) for row in BANDS], 'sale_amount_off': 29}
    with pytest.raises(ValidationError, match='lowest range price'):
        validate_pricing_config('weight_range', too_high)
