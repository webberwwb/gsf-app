"""Tests for order points calculation."""
from decimal import Decimal

from utils.order_points import calculate_order_points


class FakeOrder:
    def __init__(self, subtotal, store_credit_applied=0, shipping_fee=0, adjustment_amount=0):
        self.subtotal = Decimal(str(subtotal))
        self.store_credit_applied = Decimal(str(store_credit_applied))
        self.shipping_fee = Decimal(str(shipping_fee))
        self.adjustment_amount = Decimal(str(adjustment_amount))


def test_points_from_subtotal_only():
    assert calculate_order_points(FakeOrder(50.00)) == 5000


def test_points_exclude_shipping():
    assert calculate_order_points(FakeOrder(50.00, shipping_fee=7.99)) == 5000


def test_points_reduce_for_admin_discount():
    assert calculate_order_points(FakeOrder(50.00, adjustment_amount=-5.00)) == 4500


def test_points_exclude_positive_adjustment():
    assert calculate_order_points(FakeOrder(50.00, adjustment_amount=5.00)) == 5000


def test_points_after_store_credit():
    assert calculate_order_points(FakeOrder(50.00, store_credit_applied=20.00)) == 3000


def test_points_zero_when_fully_covered_by_credit():
    assert calculate_order_points(FakeOrder(30.00, store_credit_applied=30.00)) == 0


def test_points_never_negative():
    assert calculate_order_points(FakeOrder(10.00, store_credit_applied=25.00)) == 0


def test_points_use_paid_product_dollars_after_quantity_break():
    """3 items at $8 (list $10) earn points on $24, not $30."""
    assert calculate_order_points(FakeOrder(24.00)) == 2400


def test_points_use_sale_price_not_list_price():
    """2 items at sale $8 (list $10) earn points on $16, not $20."""
    assert calculate_order_points(FakeOrder(16.00)) == 1600
