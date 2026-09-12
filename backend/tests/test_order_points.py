"""Tests for order points calculation."""
from decimal import Decimal

from utils.order_points import calculate_order_points


class FakeLine:
    def __init__(self, total_price, quantity=1, cutting=False, cutting_fee=0):
        self.total_price = Decimal(str(total_price))
        self.quantity = quantity
        self.cutting = cutting
        self.cutting_fee = Decimal(str(cutting_fee)) if cutting else None


class FakeOrder:
    def __init__(self, subtotal, store_credit_applied=0, shipping_fee=0, adjustment_amount=0, items=None):
        self.subtotal = Decimal(str(subtotal))
        self.store_credit_applied = Decimal(str(store_credit_applied))
        self.shipping_fee = Decimal(str(shipping_fee))
        self.adjustment_amount = Decimal(str(adjustment_amount))
        self.items = items


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


def test_points_exclude_cutting_fee():
    """$148 product + $3 切分 earns points on $148."""
    order = FakeOrder(
        151.00,
        items=[FakeLine(151, quantity=1, cutting=True, cutting_fee=3)],
    )
    assert calculate_order_points(order) == 14800
