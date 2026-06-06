"""Tests for variant and substitute order line pricing."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.order_item_pricing import (
    build_priced_order_item,
    apply_fulfillment_price,
    compute_price_from_config,
    recalculate_existing_item,
    combine_order_notes,
    order_item_fields_for_merge,
)


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

    def get_active_variants(self):
        return [v for v in self.variants if getattr(v, 'is_active', True)]


class FakeVariant:
    def __init__(self, id, name, price_delta, product_id=1, is_active=True):
        self.id = id
        self.name = name
        self.price_delta = price_delta
        self.product_id = product_id
        self.is_active = is_active


def test_variant_price_delta_per_item():
    product = FakeProduct(pricing_data={'price': 10.0})
    product.variants = [FakeVariant(1, 'Large', 2.0)]

    from unittest.mock import patch

    with patch('utils.order_item_pricing.ProductVariant') as PV:
        PV.query.filter_by.return_value.first.return_value = product.variants[0]
        priced = build_priced_order_item(
            product, quantity=2, variant_id=1, accept_substitute=None, is_unavailable=False
        )
    assert priced['unit_price'] == 12.0
    assert priced['total_price'] == 24.0


def test_unavailable_declined_keeps_original_price():
    unit, total = apply_fulfillment_price(10.0, 20.0, 2, FakeProduct(), True, False)
    assert total == 20.0
    assert unit == 10.0


def test_unavailable_declined_cannot_fulfill_zero():
    unit, total = apply_fulfillment_price(10.0, 20.0, 2, FakeProduct(), True, False, cannot_fulfill=True)
    assert total == 0.0
    assert unit == 0.0


def test_substitute_per_item_pricing():
    product = FakeProduct(
        substitute_enabled=True,
        substitute_pricing_type='per_item',
        substitute_pricing_data={'price': 12.0},
    )
    unit, total = apply_fulfillment_price(10.0, 20.0, 2, product, True, True)
    assert total == 24.0
    assert unit == 12.0


def test_substitute_bundled_weight_same_model():
    product = FakeProduct(
        pricing_type='bundled_weight',
        pricing_data={'price_per_unit': 5.0, 'min_weight': 7, 'max_weight': 15},
        substitute_enabled=True,
        substitute_pricing_type='bundled_weight',
        substitute_pricing_data={'price_per_unit': 6.0, 'min_weight': 7, 'max_weight': 15},
    )
    unit, total = apply_fulfillment_price(5.0, 50.0, 1, product, True, True, final_weight=10.0)
    assert total == 60.0
    assert unit == 6.0


def test_substitute_weight_range_at_final_weight():
    product = FakeProduct(
        pricing_type='weight_range',
        pricing_data={'ranges': [{'min': 0, 'max': 5, 'price': 8.0}, {'min': 5, 'max': None, 'price': 10.0}]},
        substitute_enabled=True,
        substitute_pricing_type='weight_range',
        substitute_pricing_data={
            'ranges': [{'min': 0, 'max': 5, 'price': 9.0}, {'min': 5, 'max': None, 'price': 11.0}]
        },
    )
    sub_unit, sub_total = compute_price_from_config(
        'weight_range',
        product.substitute_pricing_data,
        quantity=1,
        final_weight=6.0,
    )
    assert sub_unit == 11.0
    assert sub_total == 11.0


class FakeItem:
    def __init__(self, **kwargs):
        self.product_id = kwargs.get('product_id', 1)
        self.quantity = kwargs.get('quantity', 1)
        self.final_weight = kwargs.get('final_weight')
        self.variant_price_delta = kwargs.get('variant_price_delta', 0)
        self.is_unavailable = kwargs.get('is_unavailable', False)
        self.accept_substitute = kwargs.get('accept_substitute')
        self.unit_price = kwargs.get('unit_price', 0)
        self.total_price = kwargs.get('total_price', 0)


def test_recalculate_existing_item_restores_weight_price():
    """Regression: line with final_weight but total_price=0 must reprice on recalc."""
    product = FakeProduct(
        pricing_type='weight_range',
        pricing_data={
            'ranges': [
                {'min': 2.5, 'max': 3.5, 'price': 29},
                {'min': 5, 'max': None, 'price': 34},
            ],
        },
    )
    item = FakeItem(final_weight=5.29, total_price=0, unit_price=0)
    recalculate_existing_item(item, product)
    assert float(item.total_price) == 34.0
    assert float(item.unit_price) == 34.0


class FakeOrder:
    def __init__(self, notes=None):
        self.notes = notes


class FakeOrderItem:
    def __init__(self, **kwargs):
        self.order_id = kwargs.get('order_id', 1)
        self.id = kwargs.get('id', 99)
        self.product_id = kwargs.get('product_id', 1)
        self.quantity = kwargs.get('quantity', 1)
        self.unit_price = kwargs.get('unit_price', 10)
        self.total_price = kwargs.get('total_price', 10)
        self.final_weight = kwargs.get('final_weight')
        self.variant_id = kwargs.get('variant_id')
        self.variant_name = kwargs.get('variant_name')
        self.variant_price_delta = kwargs.get('variant_price_delta')
        self.accept_substitute = kwargs.get('accept_substitute')
        self.is_unavailable = kwargs.get('is_unavailable', False)
        self.cannot_fulfill = kwargs.get('cannot_fulfill', False)


def test_combine_order_notes_dedupes():
    orders = [
        FakeOrder('note A'),
        FakeOrder('note B'),
        FakeOrder('note A'),
    ]
    assert combine_order_notes(orders) == 'note A\n---\nnote B'


def test_order_item_fields_for_merge_carries_variant_and_substitute():
    item = FakeOrderItem(
        variant_id=4,
        variant_name='未开膛',
        variant_price_delta=0,
        accept_substitute=False,
        is_unavailable=True,
        cannot_fulfill=True,
    )
    fields = order_item_fields_for_merge(item)
    assert fields['variant_id'] == 4
    assert fields['variant_name'] == '未开膛'
    assert fields['accept_substitute'] is False
    assert fields['is_unavailable'] is True
    assert fields['cannot_fulfill'] is True


if __name__ == '__main__':
    test_unavailable_declined_keeps_original_price()
    test_unavailable_declined_cannot_fulfill_zero()
    test_substitute_per_item_pricing()
    test_substitute_bundled_weight_same_model()
    test_substitute_weight_range_at_final_weight()
    test_recalculate_existing_item_restores_weight_price()
    test_combine_order_notes_dedupes()
    test_order_item_fields_for_merge_carries_variant_and_substitute()
    print('variant/substitute pricing tests passed')
