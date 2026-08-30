"""Quantity-break and mixed-variant pricing."""
from unittest.mock import patch

from utils.order_item_pricing import (
    lookup_break_price,
    resolve_per_item_unit,
    build_priced_order_item,
)
from utils.order_points import calculate_order_points


class FakeProduct:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.name = kwargs.get('name', 'Test')
        self.pricing_type = kwargs.get('pricing_type', 'per_item')
        self.pricing_data = kwargs.get('pricing_data', {'price': 10.0})
        self.substitute_enabled = kwargs.get('substitute_enabled', False)
        self.substitute_price = kwargs.get('substitute_price')
        self.substitute_pricing_type = kwargs.get('substitute_pricing_type')
        self.substitute_pricing_data = kwargs.get('substitute_pricing_data')
        self.variants = kwargs.get('variants', [])
        self.variants_share_price = kwargs.get('variants_share_price', True)
        self.is_discount = kwargs.get('is_discount', False)

    def get_active_variants(self):
        return [v for v in self.variants if getattr(v, 'is_active', True)]


class FakeVariant:
    def __init__(self, id, name, price_delta=0, product_id=1, is_active=True, price=None, sale_price=None, quantity_breaks=None):
        self.id = id
        self.name = name
        self.price_delta = price_delta
        self.product_id = product_id
        self.is_active = is_active
        self.price = price
        self.sale_price = sale_price
        self.quantity_breaks = quantity_breaks


class FakeOrder:
    def __init__(self, subtotal, store_credit_applied=0, shipping_fee=0, adjustment_amount=0):
        self.subtotal = subtotal
        self.store_credit_applied = store_credit_applied
        self.shipping_fee = shipping_fee
        self.adjustment_amount = adjustment_amount


def test_lookup_break_highest_matching_tier():
    breaks = [{'min_qty': 3, 'price': 8}, {'min_qty': 6, 'price': 7}]
    assert lookup_break_price(10, breaks, 1) == 10
    assert lookup_break_price(10, breaks, 2) == 10
    assert lookup_break_price(10, breaks, 3) == 8
    assert lookup_break_price(10, breaks, 6) == 7


def test_share_price_break_plus_delta():
    product = FakeProduct(pricing_data={'price': 10.0, 'quantity_breaks': [{'min_qty': 3, 'price': 8}]})
    variant = FakeVariant(1, 'Large', price_delta=2.0)
    unit, delta = resolve_per_item_unit(product, variant, 3)
    assert unit == 10.0  # 8 + 2
    assert delta == 2.0


def test_own_price_variant_break():
    product = FakeProduct(
        pricing_data={'price': 10.0},
        variants_share_price=False,
    )
    variant = FakeVariant(1, 'B', price=12.0, quantity_breaks=[{'min_qty': 3, 'price': 10}])
    unit, delta = resolve_per_item_unit(product, variant, 3)
    assert unit == 10.0
    assert delta == 2.0  # 12 - 10 snapshot


def test_mixed_variant_pooling_uses_product_qty():
    product = FakeProduct(pricing_data={'price': 10.0, 'quantity_breaks': [{'min_qty': 3, 'price': 8}]})
    variant_a = FakeVariant(1, 'A', price_delta=0)
    product.variants = [variant_a]

    with patch('utils.order_item_pricing.ProductVariant') as PV:
        PV.query.filter_by.return_value.first.return_value = variant_a
        priced = build_priced_order_item(
            product, quantity=1, variant_id=1, product_qty=3
        )
    assert priced['unit_price'] == 8.0
    assert priced['total_price'] == 8.0


def test_sale_price_is_charged_when_on_sale():
    product = FakeProduct(
        is_discount=True,
        pricing_data={'price': 10.0, 'sale_price': 8.0},
    )
    unit, _ = resolve_per_item_unit(product, None, 1)
    assert unit == 8.0


def test_sale_price_ignored_when_not_flagged():
    product = FakeProduct(
        is_discount=False,
        pricing_data={'price': 10.0, 'sale_price': 8.0},
    )
    unit, _ = resolve_per_item_unit(product, None, 1)
    assert unit == 10.0


def test_sale_only_when_deal_flag_set():
    product = FakeProduct(
        is_discount=False,
        pricing_data={'price': 10.0, 'sale_price': 8.0},
    )
    assert resolve_per_item_unit(product, None, 1)[0] == 10.0
    product._deal_is_discount = True
    assert resolve_per_item_unit(product, None, 1)[0] == 8.0
    product._deal_is_discount = False
    assert resolve_per_item_unit(product, None, 1)[0] == 10.0


def test_quantity_break_overrides_sale_base():
    product = FakeProduct(
        is_discount=True,
        pricing_data={'price': 10.0, 'sale_price': 8.0, 'quantity_breaks': [{'min_qty': 3, 'price': 7}]},
    )
    assert resolve_per_item_unit(product, None, 1)[0] == 8.0
    assert resolve_per_item_unit(product, None, 3)[0] == 7.0


def test_own_price_variant_uses_sale_price():
    product = FakeProduct(
        is_discount=True,
        pricing_data={'price': 10.0, 'sale_price': 8.0},
        variants_share_price=False,
    )
    variant = FakeVariant(1, 'B', price=12.0, sale_price=9.0)
    unit, delta = resolve_per_item_unit(product, variant, 1)
    assert unit == 9.0
    assert delta == -1.0  # 9 - 10 list


def test_points_follow_discounted_subtotal_not_list_price():
    # 3 × $8 paid (list $10) → 2400 points, not 3000
    assert calculate_order_points(FakeOrder(24.00)) == 2400


def test_points_still_exclude_shipping_on_discounted_order():
    assert calculate_order_points(FakeOrder(24.00, shipping_fee=7.99)) == 2400
