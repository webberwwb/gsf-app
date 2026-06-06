"""Round monetary amounts to 2 decimal places (half-up)."""

from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal('0.01')


def round_money(value) -> Decimal:
    if value is None:
        return Decimal('0.00')
    if isinstance(value, Decimal):
        d = value
    else:
        d = Decimal(str(value))
    return d.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def round_money_float(value) -> float:
    return float(round_money(value))
