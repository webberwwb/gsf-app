"""Per-product 切分 service: flat per-piece fee, excluded from points and free delivery."""
from decimal import Decimal

from utils.money import round_money, round_money_float


def product_offers_cutting(product):
    return bool(getattr(product, 'cutting_enabled', False))


def catalog_cutting_fee(product):
    if not product_offers_cutting(product):
        return 0.0
    try:
        return max(0.0, float(product.cutting_fee or 0))
    except (TypeError, ValueError):
        return 0.0


def resolve_cutting_choice(product, cutting):
    """Return (want_cut, fee_per_unit, error). Rejects 切分 when the product does not offer it."""
    want = bool(cutting)
    if not product_offers_cutting(product):
        if want:
            name = getattr(product, 'name', None) or getattr(product, 'id', '')
            return False, 0.0, f'商品「{name}」不提供切分服务'
        return False, 0.0, None
    fee = catalog_cutting_fee(product) if want else 0.0
    return want, fee, None


def apply_cutting_surcharge(unit_price, total_price, quantity, pricing_type, cutting, cutting_fee):
    """Add a flat per-qty fee. For per_item, also bump unit_price. Weight types keep the $/lb rate."""
    if not cutting:
        return unit_price, total_price, 0.0
    try:
        fee = max(0.0, float(cutting_fee or 0))
    except (TypeError, ValueError):
        fee = 0.0
    if fee <= 0:
        return unit_price, total_price, 0.0
    qty = int(quantity or 1)
    extra = round_money_float(fee * qty)
    if pricing_type == 'per_item':
        unit_price = round_money_float(float(unit_price or 0) + fee)
    total_price = round_money_float(float(total_price or 0) + extra)
    return unit_price, total_price, fee


def _item_flag(item, name, default=False):
    if isinstance(item, dict):
        return bool(item.get(name, default))
    return bool(getattr(item, name, default))


def _item_number(item, name, default=0):
    if isinstance(item, dict):
        raw = item.get(name, default)
    else:
        raw = getattr(item, name, default)
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def line_cutting_total(item):
    """Snapshot fee × quantity when the line is 切分; else 0."""
    if not _item_flag(item, 'cutting'):
        return Decimal('0')
    fee = _item_number(item, 'cutting_fee')
    if isinstance(item, dict):
        qty = item.get('quantity', 1)
    else:
        qty = getattr(item, 'quantity', 1)
    try:
        qty = int(qty or 1)
    except (TypeError, ValueError):
        qty = 1
    return round_money(Decimal(str(fee)) * qty)


def items_cutting_total(items):
    total = Decimal('0')
    for item in items or []:
        total += line_cutting_total(item)
    return round_money(total)


def order_cutting_fees_total(order):
    items = getattr(order, 'items', None)
    if not items:
        return Decimal('0')
    return items_cutting_total(items)


def line_product_amount(item, line_total=None):
    """Line dollars that count as product (excludes 切分)."""
    if line_total is None:
        if isinstance(item, dict):
            raw = item.get('total_price', 0)
        else:
            raw = getattr(item, 'total_price', 0)
        line_total = Decimal(str(raw or 0))
    else:
        line_total = Decimal(str(line_total or 0))
    product = line_total - line_cutting_total(item)
    return round_money(max(Decimal('0'), product))
