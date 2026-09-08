"""推荐官 self-buy: pay catalog/sale price minus their commission."""
from decimal import Decimal

from utils.money import round_money


def _as_decimal(value):
    if value is None:
        return Decimal('0')
    return Decimal(str(value))


def _floor_money(value, amount):
    return float(round_money(max(Decimal('0'), _as_decimal(value) - _as_decimal(amount))))


def attach_influencer_buyer_discount(product, user_id=None):
    """Mark a product so paid pricing subtracts this buyer's 推荐官 rate."""
    if product is None:
        return product
    if hasattr(product, '_influencer_discount'):
        delattr(product, '_influencer_discount')
    if not user_id:
        return product
    from models.user import User
    from services.influencer_service import resolve_rate

    user = User.query.get(user_id)
    if not user or not user.is_influencer:
        return product
    resolved = resolve_rate(user.id, product.id)
    if resolved:
        product._influencer_discount = resolved
    return product


def apply_influencer_unit_discount(product, unit_price, pricing_type=None):
    """Subtract a matching per-unit commission from a paid unit price."""
    disc = getattr(product, '_influencer_discount', None) if product else None
    if not disc:
        return unit_price
    commission_type, amount = disc
    pt = pricing_type or getattr(product, 'pricing_type', None)
    from models.influencer import COMMISSION_PER_WEIGHT

    if commission_type == COMMISSION_PER_WEIGHT:
        if pt in ('unit_weight', 'bundled_weight', 'per_item', 'weight_range'):
            return _floor_money(unit_price, amount)
        return unit_price
    if pt in ('per_item', 'weight_range'):
        return _floor_money(unit_price, amount)
    return unit_price


def apply_influencer_line_discount(product, unit_price, total_price, quantity):
    """Per-item commission on a per-lb product only reduces the line total."""
    disc = getattr(product, '_influencer_discount', None) if product else None
    if not disc:
        return unit_price, total_price
    commission_type, amount = disc
    from models.influencer import COMMISSION_PER_ITEM

    pt = getattr(product, 'pricing_type', None)
    if commission_type == COMMISSION_PER_ITEM and pt in ('unit_weight', 'bundled_weight'):
        qty = max(int(quantity or 1), 0)
        total_price = _floor_money(total_price, _as_decimal(amount) * qty)
    return unit_price, total_price


def apply_rate_to_pricing_data(pricing_type, pricing_data, commission_type, amount):
    """Return a copy of pricing_data with paid units reduced by the commission."""
    pd = dict(pricing_data or {})
    from models.influencer import COMMISSION_PER_WEIGHT

    if commission_type == COMMISSION_PER_WEIGHT:
        if pricing_type in ('unit_weight', 'bundled_weight'):
            if pd.get('price_per_unit') is not None:
                pd['price_per_unit'] = _floor_money(pd['price_per_unit'], amount)
            if pd.get('sale_price_per_unit') is not None:
                pd['sale_price_per_unit'] = _floor_money(pd['sale_price_per_unit'], amount)
        elif pricing_type == 'weight_range':
            pd['ranges'] = [
                {**row, 'price': _floor_money(row.get('price'), amount)}
                for row in (pd.get('ranges') or [])
            ]
        else:
            if pd.get('price') is not None:
                pd['price'] = _floor_money(pd['price'], amount)
            if pd.get('sale_price') is not None:
                pd['sale_price'] = _floor_money(pd['sale_price'], amount)
        return pd

    if pricing_type in ('unit_weight', 'bundled_weight'):
        return pd
    if pd.get('price') is not None:
        pd['price'] = _floor_money(pd['price'], amount)
    if pd.get('sale_price') is not None:
        pd['sale_price'] = _floor_money(pd['sale_price'], amount)
    if pd.get('ranges'):
        pd['ranges'] = [
            {**row, 'price': _floor_money(row.get('price'), amount)}
            for row in pd['ranges']
        ]
    if pd.get('quantity_breaks'):
        pd['quantity_breaks'] = [
            {**row, 'price': _floor_money(row.get('price'), amount)}
            for row in pd['quantity_breaks']
        ]
    return pd


def apply_influencer_discount_to_product_payload(data, influencer_user_id):
    """Adjust a serialized product so the app shows 推荐官价 and compare-at."""
    if not data or not influencer_user_id:
        return data
    from models.user import User
    from services.influencer_service import resolve_rate
    from models.influencer import COMMISSION_PER_WEIGHT

    user = User.query.get(influencer_user_id)
    if not user or not user.is_influencer:
        return data
    resolved = resolve_rate(influencer_user_id, data.get('id'))
    if not resolved:
        return data
    commission_type, amount = resolved
    amount_f = float(round_money(amount))
    if amount_f <= 0:
        return data

    pd = dict(data.get('pricing_data') or {})
    pt = data.get('pricing_type')
    on_sale = bool(data.get('is_discount'))

    if pt in ('unit_weight', 'bundled_weight'):
        list_unit = pd.get('price_per_unit')
        paid_unit = pd.get('sale_price_per_unit') if on_sale and pd.get('sale_price_per_unit') is not None else list_unit
        if commission_type == COMMISSION_PER_WEIGHT and paid_unit is not None:
            pd['sale_price_per_unit'] = _floor_money(paid_unit, amount)
            data['sale_price'] = pd['sale_price_per_unit']
            data['display_price'] = pd['sale_price_per_unit']
            data['price'] = pd['sale_price_per_unit']
            if data.get('original_price') is None:
                data['original_price'] = float(list_unit) if list_unit is not None else None
    else:
        list_price = pd.get('price')
        paid = pd.get('sale_price') if on_sale and pd.get('sale_price') is not None else list_price
        if paid is not None:
            discounted = _floor_money(paid, amount)
            pd['sale_price'] = discounted
            data['sale_price'] = discounted
            data['display_price'] = discounted
            data['price'] = discounted
            if data.get('original_price') is None:
                data['original_price'] = float(list_price) if list_price is not None else None
        if pd.get('ranges'):
            pd['ranges'] = [
                {**row, 'price': _floor_money(row.get('price'), amount)}
                for row in pd['ranges']
            ]
        if pd.get('quantity_breaks'):
            pd['quantity_breaks'] = [
                {**row, 'price': _floor_money(row.get('price'), amount)}
                for row in pd['quantity_breaks']
            ]
        for variant in data.get('variants') or []:
            if commission_type == COMMISSION_PER_WEIGHT:
                continue
            base = variant.get('sale_price') if on_sale and variant.get('sale_price') is not None else variant.get('price')
            if base is not None:
                variant['sale_price'] = _floor_money(base, amount)

    data['pricing_data'] = pd
    data['influencer_discount'] = True
    data['influencer_commission_type'] = commission_type
    data['influencer_commission_amount'] = amount_f
    return data
