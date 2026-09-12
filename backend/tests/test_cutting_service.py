"""Unit tests for per-product 切分 fee and validation."""
from decimal import Decimal

from utils.cutting import (
    apply_cutting_surcharge,
    line_cutting_total,
    line_product_amount,
    resolve_cutting_choice,
)


class FakeProduct:
    def __init__(self, name='鱼', cutting_enabled=True, cutting_fee=2):
        self.name = name
        self.cutting_enabled = cutting_enabled
        self.cutting_fee = cutting_fee


def test_reject_cutting_when_disabled():
    want, fee, err = resolve_cutting_choice(FakeProduct(cutting_enabled=False), True)
    assert want is False
    assert fee == 0
    assert '不提供切分' in err


def test_allow_uncut_when_disabled():
    want, fee, err = resolve_cutting_choice(FakeProduct(cutting_enabled=False), False)
    assert want is False
    assert fee == 0
    assert err is None


def test_per_item_adds_fee_to_unit_and_total():
    unit, total, snap = apply_cutting_surcharge(10, 20, 2, 'per_item', True, 2)
    assert unit == 12
    assert total == 24
    assert snap == 2


def test_weight_adds_fee_to_total_only():
    unit, total, snap = apply_cutting_surcharge(5.5, 5.5, 1, 'unit_weight', True, 3)
    assert unit == 5.5
    assert total == 8.5
    assert snap == 3


def test_line_product_amount_strips_cutting():
    item = {'cutting': True, 'cutting_fee': 3, 'quantity': 1, 'total_price': 151}
    assert line_cutting_total(item) == Decimal('3.00')
    assert line_product_amount(item) == Decimal('148.00')
