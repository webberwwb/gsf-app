"""Shared order line pricing: base product price, variants, and substitute fulfillment."""
import copy
from decimal import Decimal
from utils.money import round_money, round_money_float
from utils.image_urls import public_image_url, public_image_urls, thumbnail_url, thumbnail_urls
from models.product_variant import ProductVariant
from models.product import Product
from models.order import OrderItem
from utils.cutting import apply_cutting_surcharge, resolve_cutting_choice


def _parse_final_weight(final_weight):
    if final_weight is None:
        return None
    try:
        w = float(final_weight)
        return w if w > 0 else None
    except (ValueError, TypeError):
        return None


def _safe_float(value, default=0.0):
    """Coerce pricing JSON values; None or invalid → default."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _optional_float(value):
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def product_on_sale(product):
    """True when this product is on sale in the current deal context.

    Catalog products are never on sale by themselves. Pass deal context via
    product._deal_is_discount, or (for tests) product.is_discount.
    """
    if product is None:
        return False
    if getattr(product, '_deal_is_discount', None) is not None:
        return bool(product._deal_is_discount)
    return bool(getattr(product, 'is_discount', False))


def attach_deal_sale(product, group_deal_id=None, deal_product=None):
    """Mark a product instance with this deal's sale flag for pricing."""
    if product is None:
        return product
    on_sale = False
    if deal_product is not None:
        on_sale = bool(getattr(deal_product, 'is_discount', False))
    elif group_deal_id:
        from models.groupdeal import GroupDealProduct
        dp = GroupDealProduct.query.filter_by(
            group_deal_id=group_deal_id,
            product_id=getattr(product, 'id', None),
        ).first()
        on_sale = bool(dp and dp.is_discount)
    product._deal_is_discount = on_sale
    return product


def paid_pricing_data(product, pricing_data=None):
    """Copy of pricing_data with sale fields applied when the product is on sale."""
    pd = dict(pricing_data if pricing_data is not None else (getattr(product, 'pricing_data', None) or {}))
    pricing_type = getattr(product, 'pricing_type', None)
    if product_on_sale(product):
        if pricing_type == 'per_item':
            sale = _optional_float(pd.get('sale_price'))
            if sale is not None:
                pd['price'] = sale
        elif pricing_type in ('unit_weight', 'bundled_weight'):
            sale = _optional_float(pd.get('sale_price_per_unit'))
            if sale is not None:
                pd['price_per_unit'] = sale
        elif pricing_type == 'weight_range':
            off = _optional_float(pd.get('sale_amount_off'))
            if off is not None and off > 0:
                pd['ranges'] = [
                    {**row, 'price': _floor_paid(row.get('price'), off)}
                    for row in (pd.get('ranges') or [])
                    if isinstance(row, dict)
                ]
    disc = getattr(product, '_influencer_discount', None)
    if disc:
        from utils.influencer_pricing import apply_rate_to_pricing_data
        commission_type, amount = disc
        pd = apply_rate_to_pricing_data(pricing_type, pd, commission_type, amount)
    return pd


def get_display_price_from_config(pricing_type, pricing_data):
    """Default display price for a pricing_type + pricing_data config."""
    from utils.money import round_money_float

    pricing_data = pricing_data or {}
    if pricing_type == 'per_item':
        if pricing_data.get('price') is None:
            return None
        return round_money_float(_safe_float(pricing_data.get('price'), 0))
    if pricing_type == 'weight_range':
        ranges = pricing_data.get('ranges') or []
        if ranges:
            return round_money_float(_lowest_band_price(ranges))
        return None
    if pricing_type == 'unit_weight':
        if pricing_data.get('price_per_unit') is None:
            return None
        return round_money_float(_safe_float(pricing_data.get('price_per_unit'), 0))
    if pricing_type == 'bundled_weight':
        if pricing_data.get('price_per_unit') is None:
            return None
        price_per_unit = _safe_float(pricing_data.get('price_per_unit'), 0)
        min_weight = _safe_float(pricing_data.get('min_weight'), 7)
        max_weight = _safe_float(pricing_data.get('max_weight'), 15)
        return round_money_float(price_per_unit * ((min_weight + max_weight) / 2))
    return None


def _lowest_band_price(ranges):
    if not ranges:
        return 0.0
    prices = [_safe_float(r.get('price'), 0) for r in ranges]
    return min(prices) if prices else 0.0


WEIGHT_PRICING_TYPES = ('weight_range', 'unit_weight', 'bundled_weight')


def normalize_quantity_breaks(breaks):
    """Return sorted [{min_qty, price}, ...] ignoring invalid rows."""
    if not breaks or not isinstance(breaks, list):
        return []
    out = []
    seen = set()
    for row in breaks:
        if not isinstance(row, dict):
            continue
        try:
            min_qty = int(row.get('min_qty'))
            price = float(row.get('price'))
        except (TypeError, ValueError):
            continue
        if min_qty < 2 or price < 0 or min_qty in seen:
            continue
        seen.add(min_qty)
        out.append({'min_qty': min_qty, 'price': price})
    out.sort(key=lambda x: x['min_qty'])
    return out


def lookup_break_price(base_price, breaks, product_qty):
    """Highest matching min_qty wins; otherwise base_price."""
    unit = _safe_float(base_price, 0)
    qty = int(product_qty or 1)
    for row in normalize_quantity_breaks(breaks):
        if qty >= row['min_qty']:
            unit = row['price']
    return unit


def product_shares_variant_price(product):
    share = getattr(product, 'variants_share_price', True)
    return True if share is None else bool(share)


def pooled_product_qty_for_item(item, product_qty=None):
    """Total qty of this product on the order (all variant lines)."""
    if product_qty is not None:
        try:
            return max(1, int(product_qty))
        except (TypeError, ValueError):
            pass
    order_id = getattr(item, 'order_id', None)
    product_id = getattr(item, 'product_id', None)
    if order_id and product_id:
        try:
            from utils.order_audit import active_items_for_order
            siblings = active_items_for_order(order_id)
            total = sum(int(i.quantity or 0) for i in siblings if i.product_id == product_id)
            if total > 0:
                return total
        except Exception:
            pass
    try:
        return max(1, int(item.quantity or 1))
    except (TypeError, ValueError):
        return 1


def _paid_per_item_base(product, variant=None):
    """Paid unit base (before quantity breaks) and catalog list price."""
    pd = product.pricing_data or {}
    list_price = _safe_float(pd.get('price'), 0)
    sale = _optional_float(pd.get('sale_price'))
    product_base = sale if product_on_sale(product) and sale is not None else list_price
    share = product_shares_variant_price(product)

    if variant is not None and not share:
        variant_list = getattr(variant, 'price', None)
        if variant_list is None:
            variant_list = list_price + _safe_float(getattr(variant, 'price_delta', 0), 0)
        variant_list = _safe_float(variant_list, 0)
        variant_sale = _optional_float(getattr(variant, 'sale_price', None))
        base = variant_sale if product_on_sale(product) and variant_sale is not None else variant_list
        return base, list_price

    return product_base, list_price


def resolve_per_item_unit(product, variant, product_qty, snapshot_delta=None):
    """
    Paid per-item unit price after quantity breaks.
    Returns (unit_price, snapshot_delta).
    """
    pd = product.pricing_data or {}
    qty = int(product_qty or 1)
    share = product_shares_variant_price(product)
    product_base, list_price = _paid_per_item_base(product, None)

    if variant is not None and not share:
        base, _ = _paid_per_item_base(product, variant)
        breaks = getattr(variant, 'quantity_breaks', None)
        unit = lookup_break_price(base, breaks, qty)
        delta = round_money_float(base - list_price)
        from utils.influencer_pricing import apply_influencer_unit_discount
        unit = apply_influencer_unit_discount(product, unit, 'per_item')
        return round_money_float(unit), delta

    unit = lookup_break_price(product_base, pd.get('quantity_breaks'), qty)
    if variant is not None:
        delta = _safe_float(getattr(variant, 'price_delta', 0), 0)
    elif snapshot_delta is not None:
        delta = _safe_float(snapshot_delta, 0)
    else:
        delta = 0.0
    from utils.influencer_pricing import apply_influencer_unit_discount
    unit = apply_influencer_unit_discount(product, unit + delta, 'per_item')
    return round_money_float(unit), round_money_float(delta)


def expand_request_items(items, products=None):
    """Split weight-based lines so each physical item is quantity=1."""
    from utils.query_batch import products_by_ids

    if products is None:
        products = products_by_ids(item_data.get('product_id') for item_data in items)
    expanded = []
    for item_data in items:
        product = products.get(item_data['product_id'])
        if not product:
            raise ValueError(f'Product {item_data["product_id"]} not found')
        qty = int(item_data.get('quantity') or 1)
        pt = item_data.get('pricing_type') or product.pricing_type
        if pt in WEIGHT_PRICING_TYPES and qty > 1:
            for _ in range(qty):
                row = dict(item_data)
                row['quantity'] = 1
                expanded.append(row)
        else:
            expanded.append(item_data)
    return expanded


def compute_price_from_config(pricing_type, pricing_data, quantity=1, final_weight=None):
    """
    Compute unit_price and total_price from pricing_type + pricing_data.
    Returns (unit_price: float, total_price: float).
    """
    quantity = int(quantity or 1)
    fw = _parse_final_weight(final_weight)
    pricing_data = pricing_data or {}

    if pricing_type == 'per_item':
        unit_price = _safe_float(get_display_price_from_config(pricing_type, pricing_data), 0)
        total_price = unit_price * quantity
    elif pricing_type == 'weight_range':
        ranges = pricing_data.get('ranges', [])
        if fw is not None and ranges:
            matched_price = None
            for range_item in ranges:
                min_weight = _safe_float(range_item.get('min'), 0)
                max_weight = range_item.get('max')
                if fw >= min_weight and (max_weight is None or fw < max_weight):
                    matched_price = _safe_float(range_item.get('price'), 0)
                    break
            unit_price = matched_price if matched_price is not None else _lowest_band_price(ranges)
        else:
            unit_price = _lowest_band_price(ranges)
        total_price = unit_price * quantity
    elif pricing_type == 'unit_weight':
        price_per_unit = _safe_float(pricing_data.get('price_per_unit'), 0)
        unit_price = price_per_unit
        weight = fw if fw is not None else 1
        total_price = price_per_unit * weight
    elif pricing_type == 'bundled_weight':
        price_per_unit = _safe_float(pricing_data.get('price_per_unit'), 0)
        unit_price = price_per_unit
        if fw is not None and price_per_unit > 0:
            total_price = price_per_unit * fw
        elif price_per_unit > 0:
            min_weight = _safe_float(pricing_data.get('min_weight'), 7)
            total_price = price_per_unit * min_weight
        else:
            total_price = 0
    else:
        unit_price = _safe_float(get_display_price_from_config(pricing_type, pricing_data), 0)
        total_price = unit_price * quantity

    return round_money_float(unit_price), round_money_float(total_price)


def compute_base_price(product, quantity, pricing_type=None, final_weight=None):
    """Compute base unit_price and total_price from a Product (no variant/substitute)."""
    pricing_type = pricing_type or product.pricing_type
    return compute_price_from_config(
        pricing_type, paid_pricing_data(product), quantity, final_weight
    )


def get_substitute_pricing(product):
    """Return (pricing_type, pricing_data) for substitute fulfillment."""
    if product.substitute_pricing_data:
        ptype = product.substitute_pricing_type or product.pricing_type
        return ptype, product.substitute_pricing_data
    if product.substitute_price is not None:
        return 'per_item', {'price': _safe_float(product.substitute_price, 0)}
    return product.pricing_type, product.pricing_data or {}


def apply_variant_delta_safe(unit_price, total_price, variant_price_delta, pricing_type, quantity, final_weight, product=None):
    delta = float(variant_price_delta or 0)
    if delta == 0:
        return unit_price, total_price

    unit_price = unit_price + delta
    if pricing_type in ('per_item', 'weight_range'):
        total_price = unit_price * int(quantity or 1)
    elif pricing_type == 'unit_weight':
        fw = _parse_final_weight(final_weight)
        weight = fw if fw is not None else 1
        total_price = unit_price * weight
    elif pricing_type == 'bundled_weight':
        fw = _parse_final_weight(final_weight)
        if fw is not None:
            total_price = unit_price * fw
        elif product and product.pricing_data:
            min_weight = float(product.pricing_data.get('min_weight', 7))
            total_price = unit_price * min_weight
        else:
            total_price = unit_price * 7
    return unit_price, total_price


def apply_fulfillment_price(
    unit_price,
    base_total,
    quantity,
    product,
    is_unavailable,
    accept_substitute,
    final_weight=None,
    pricing_type=None,
    cannot_fulfill=False,
):
    """Apply unavailable / substitute pricing rules."""
    if not is_unavailable:
        return unit_price, base_total

    if cannot_fulfill:
        return 0.0, 0.0

    if accept_substitute is not True:
        return unit_price, base_total

    sub_type, sub_data = get_substitute_pricing(product)
    # Substitute uses same pricing model shape; same qty/weight as the order line
    line_pricing_type = pricing_type or product.pricing_type
    sub_unit, sub_total = compute_price_from_config(
        sub_type,
        sub_data,
        quantity,
        final_weight,
    )
    return sub_unit, max(0.0, float(sub_total))


def resolve_variant(product, variant_id, *, required=True, variant_rows=None):
    """
    Validate variant selection. Returns (variant, error_message).
    variant is None if no active variants on product.
    When required=False (admin edits), lines may omit variant_id on variant products.
    variant_rows, when set, is used instead of the database so a proposed price can be quoted.
    """
    if variant_rows is not None:
        active = [v for v in variant_rows if getattr(v, 'is_active', True) is not False]
    elif hasattr(product, 'get_active_variants'):
        active = product.get_active_variants()
    else:
        active = [v for v in (product.variants or []) if v.is_active]

    if not active:
        if variant_id:
            return None, f'Product {product.id} has no variants'
        return None, None

    if not variant_id:
        if required:
            return None, f'请为商品「{product.name}」选择选项'
        return None, None

    if variant_rows is not None:
        variant = next(
            (v for v in active if v.id == variant_id or str(v.id) == str(variant_id)),
            None,
        )
    else:
        variant = ProductVariant.query.filter_by(id=variant_id, product_id=product.id, is_active=True).first()
    if not variant:
        return None, f'Invalid variant {variant_id} for product {product.id}'
    return variant, None


def validate_substitute_preference(product, accept_substitute):
    if product.substitute_enabled:
        if accept_substitute is None:
            return f'请确认商品「{product.name}」是否接受备选产品'
        return None
    if accept_substitute is not None:
        return f'Product {product.id} does not offer substitutes'
    return None


def _floor_paid(value, amount):
    return float(round_money(max(Decimal('0'), Decimal(str(value or 0)) - Decimal(str(amount or 0)))))


class _SnapVariant:
    def __init__(self, data):
        data = data or {}
        self.id = data.get('id')
        self.name = data.get('name')
        self.price = data.get('price')
        self.sale_price = data.get('sale_price')
        self.price_delta = data.get('price_delta') or 0
        self.quantity_breaks = data.get('quantity_breaks')
        self.is_active = True
        self.product_id = None


class _SnapProduct:
    """Stand-in product whose prices come only from a line snapshot."""

    def __init__(self, snap):
        snap = snap or {}
        self.id = None
        self.name = ''
        self.pricing_type = snap.get('pricing_type') or 'per_item'
        self.pricing_data = snap.get('pricing_data') or {}
        self.variants_share_price = snap.get('variants_share_price', True)
        self.substitute_enabled = bool(snap.get('substitute_pricing_data'))
        self.substitute_pricing_type = snap.get('substitute_pricing_type')
        self.substitute_pricing_data = snap.get('substitute_pricing_data')
        self.substitute_price = None
        self._deal_is_discount = False
        self.counts_toward_free_shipping = snap.get('counts_toward_free_shipping', True)
        self.cutting_enabled = False
        self.cutting_fee = 0
        variant = snap.get('variant')
        self._variant = _SnapVariant(variant) if variant else None

    def get_active_variants(self):
        return [self._variant] if self._variant else []


def build_pricing_snapshot(product, variant=None):
    """Paid schedule for a line. Sale and per-unit influencer discount are already applied."""
    paid = copy.deepcopy(paid_pricing_data(product))
    share = product_shares_variant_price(product)
    variant_snap = None
    if variant is not None:
        v_price = _optional_float(getattr(variant, 'price', None))
        v_sale = _optional_float(getattr(variant, 'sale_price', None))
        v_breaks = copy.deepcopy(getattr(variant, 'quantity_breaks', None))
        v_delta = _safe_float(getattr(variant, 'price_delta', 0), 0)
        if not share:
            if product_on_sale(product) and v_sale is not None:
                v_price = v_sale
            v_sale = None
            disc = getattr(product, '_influencer_discount', None)
            if disc and product.pricing_type in ('per_item', 'weight_range'):
                _commission_type, amount = disc
                if v_price is not None:
                    v_price = _floor_paid(v_price, amount)
                if v_breaks:
                    v_breaks = [
                        {**row, 'price': _floor_paid(row.get('price'), amount)}
                        for row in v_breaks
                    ]
        variant_snap = {
            'id': getattr(variant, 'id', None),
            'name': getattr(variant, 'name', None),
            'price': v_price,
            'sale_price': None,
            'price_delta': v_delta,
            'quantity_breaks': v_breaks,
        }

    sub_type = None
    sub_data = None
    if getattr(product, 'substitute_enabled', False):
        sub_type, sub_data = get_substitute_pricing(product)
        sub_data = copy.deepcopy(sub_data)

    line_discount = None
    disc = getattr(product, '_influencer_discount', None)
    if disc:
        from models.influencer import COMMISSION_PER_ITEM
        commission_type, amount = disc
        if commission_type == COMMISSION_PER_ITEM and product.pricing_type in ('unit_weight', 'bundled_weight'):
            line_discount = {'amount': float(amount)}

    return {
        'pricing_type': getattr(product, 'pricing_type', None) or 'per_item',
        'pricing_data': paid,
        'variants_share_price': share,
        'variant': variant_snap,
        'substitute_pricing_type': sub_type,
        'substitute_pricing_data': sub_data,
        'counts_toward_free_shipping': getattr(product, 'counts_toward_free_shipping', True) is not False,
        'influencer_line_discount': line_discount,
        'synthetic': False,
    }


def synthetic_snapshot_from_stored(item, product=None):
    """Flat schedule that reproduces the price already stored on an old line."""
    pricing_type = (getattr(product, 'pricing_type', None) if product else None) or 'per_item'
    unit = _safe_float(getattr(item, 'unit_price', 0), 0)
    cutting = bool(getattr(item, 'cutting', False))
    fee = _safe_float(getattr(item, 'cutting_fee', 0), 0) if cutting else 0.0
    if pricing_type == 'per_item':
        pricing_data = {'price': round_money_float(max(0.0, unit - fee))}
    elif pricing_type == 'unit_weight':
        pricing_data = {'price_per_unit': unit, 'unit': 'lb'}
    elif pricing_type == 'bundled_weight':
        weight = _parse_final_weight(getattr(item, 'final_weight', None)) or 1
        pricing_data = {
            'price_per_unit': unit,
            'unit': 'lb',
            'min_weight': weight,
            'max_weight': weight,
        }
    elif pricing_type == 'weight_range':
        pricing_data = {'ranges': [{'min': 0, 'max': None, 'price': unit}]}
    else:
        pricing_data = {'price': unit}
    return {
        'pricing_type': pricing_type,
        'pricing_data': pricing_data,
        'variants_share_price': True,
        'variant': None,
        'substitute_pricing_type': None,
        'substitute_pricing_data': None,
        'counts_toward_free_shipping': (
            True if product is None else getattr(product, 'counts_toward_free_shipping', True) is not False
        ),
        'influencer_line_discount': None,
        'synthetic': True,
    }


def _apply_snapshot_line_discount(snap, unit_price, total_price, quantity, cannot_fulfill):
    if cannot_fulfill:
        return unit_price, total_price
    line_discount = (snap or {}).get('influencer_line_discount') or None
    if not line_discount:
        return unit_price, total_price
    amount = _safe_float(line_discount.get('amount'), 0)
    if amount <= 0:
        return unit_price, total_price
    qty = int(quantity or 1)
    total_price = round_money_float(max(0.0, float(total_price) - amount * qty))
    return unit_price, total_price


def price_from_snapshot(
    snap,
    quantity,
    final_weight=None,
    *,
    product_qty=None,
    is_unavailable=False,
    accept_substitute=None,
    cannot_fulfill=False,
    cutting=False,
    cutting_fee=None,
):
    """Recompute a line from its saved schedule. Does not read the live catalog."""
    product = _SnapProduct(snap)
    pricing_type = product.pricing_type
    pooled = int(product_qty if product_qty is not None else quantity or 1)
    variant = None if (snap or {}).get('synthetic') else product._variant

    if pricing_type == 'per_item':
        unit_price, _delta = resolve_per_item_unit(product, variant, pooled, snapshot_delta=0)
        base_total = round_money_float(unit_price * int(quantity or 1))
    else:
        unit_price, base_total = compute_price_from_config(
            pricing_type, product.pricing_data, quantity, final_weight
        )
        if variant is not None:
            unit_price, base_total = apply_variant_delta_safe(
                unit_price,
                base_total,
                float(variant.price_delta or 0),
                pricing_type,
                quantity,
                final_weight,
                product,
            )

    unit_price, total_price = apply_fulfillment_price(
        unit_price,
        base_total,
        quantity,
        product,
        is_unavailable,
        accept_substitute,
        final_weight=final_weight,
        pricing_type=pricing_type,
        cannot_fulfill=cannot_fulfill,
    )
    unit_price, total_price = _apply_snapshot_line_discount(
        snap, unit_price, total_price, quantity, cannot_fulfill
    )
    fee_out = 0.0
    if cutting and not cannot_fulfill:
        unit_price, total_price, fee_out = apply_cutting_surcharge(
            unit_price, total_price, quantity, pricing_type, True, cutting_fee or 0
        )
    return round_money_float(unit_price), round_money_float(total_price), fee_out


def _snapshot_variant_id(snap):
    variant = (snap or {}).get('variant') if isinstance(snap, dict) else None
    if not isinstance(variant, dict):
        return None
    return variant.get('id')


def _line_variant_changed(item, snap):
    if not snap or snap.get('synthetic'):
        return False
    item_vid = getattr(item, 'variant_id', None)
    snap_vid = _snapshot_variant_id(snap)
    if item_vid and snap_vid and int(item_vid) != int(snap_vid):
        return True
    if item_vid and not snap.get('variant'):
        return True
    return False


def build_priced_order_item(
    product,
    quantity,
    pricing_type=None,
    final_weight=None,
    variant_id=None,
    accept_substitute=None,
    cutting=False,
    is_unavailable=False,
    cannot_fulfill=False,
    require_variant=True,
    product_qty=None,
    variant_rows=None,
):
    """
    Build dict of order item fields with prices and snapshots.
    Raises ValueError on validation errors.
    product_qty: total units of this product on the order (all variants); defaults to quantity.
    """
    variant, err = resolve_variant(product, variant_id, required=require_variant, variant_rows=variant_rows)
    if err:
        raise ValueError(err)

    err = validate_substitute_preference(product, accept_substitute)
    if err:
        raise ValueError(err)

    want_cut, cutting_fee, cut_err = resolve_cutting_choice(product, cutting)
    if cut_err:
        raise ValueError(cut_err)

    pricing_type = pricing_type or product.pricing_type
    pooled_qty = int(product_qty) if product_qty is not None else int(quantity or 1)

    if pricing_type == 'per_item':
        unit_price, variant_delta = resolve_per_item_unit(product, variant, pooled_qty)
        base_total = round_money_float(unit_price * int(quantity or 1))
        if variant is None:
            variant_delta = None
    else:
        unit_price, base_total = compute_base_price(product, quantity, pricing_type, final_weight)
        variant_delta = float(variant.price_delta) if variant else 0
        unit_price, base_total = apply_variant_delta_safe(
            unit_price, base_total, variant_delta, pricing_type, quantity, final_weight, product
        )
        if variant is None:
            variant_delta = None

    unit_price, total_price = apply_fulfillment_price(
        unit_price,
        base_total,
        quantity,
        product,
        is_unavailable,
        accept_substitute,
        final_weight=final_weight,
        pricing_type=pricing_type,
        cannot_fulfill=cannot_fulfill,
    )
    from utils.influencer_pricing import apply_influencer_line_discount
    unit_price, total_price = apply_influencer_line_discount(
        product, unit_price, total_price, quantity
    )
    snap_fee = 0.0
    if not cannot_fulfill:
        unit_price, total_price, snap_fee = apply_cutting_surcharge(
            unit_price, total_price, quantity, pricing_type, want_cut, cutting_fee
        )

    return {
        'product_id': product.id,
        'product': product,
        'quantity': quantity,
        'unit_price': round_money_float(unit_price),
        'total_price': round_money_float(total_price),
        'final_weight': _parse_final_weight(final_weight),
        'variant_id': variant.id if variant else None,
        'variant_name': variant.name if variant else None,
        'variant_price_delta': variant_delta if variant else None,
        'cutting': want_cut,
        'cutting_fee': snap_fee if want_cut else None,
        'accept_substitute': accept_substitute if product.substitute_enabled else None,
        'is_unavailable': bool(is_unavailable),
        'cannot_fulfill': bool(cannot_fulfill),
        'pricing_snapshot': build_pricing_snapshot(product, variant),
        'price_choice': None,
    }


def _order_for_item(item):
    order = getattr(item, 'order', None)
    if order is None and getattr(item, 'order_id', None):
        from models.order import Order
        order = Order.query.get(item.order_id)
    return order


def resnapshot_item_from_catalog(item, product, order=None, *, list_price_only=False):
    """Replace the line schedule with the catalog price for its current variant.

    list_price_only writes the catalog list schedule. The open-order price
    choice uses that so a sale amount is not baked in by 使用新价.
    """
    from utils.influencer_pricing import attach_influencer_buyer_discount

    order = order or _order_for_item(item)
    prev_sale = getattr(product, '_deal_is_discount', None)
    if list_price_only:
        product._deal_is_discount = False
    else:
        attach_deal_sale(product, group_deal_id=getattr(order, 'group_deal_id', None))
    attach_influencer_buyer_discount(product, getattr(order, 'user_id', None))
    variant = None
    variant_id = getattr(item, 'variant_id', None)
    if variant_id:
        variant = ProductVariant.query.filter_by(id=variant_id, product_id=product.id).first()
    item.pricing_snapshot = build_pricing_snapshot(product, variant)
    if list_price_only:
        if prev_sale is None and hasattr(product, '_deal_is_discount'):
            delattr(product, '_deal_is_discount')
        else:
            product._deal_is_discount = prev_sale
    if variant is not None:
        item.variant_name = variant.name
        item.variant_price_delta = variant.price_delta
    return item.pricing_snapshot


def recalculate_existing_item(item, product=None, product_qty=None):
    """Recalculate a line from its saved schedule, not the live catalog."""
    from utils.order_lock import order_money_locked
    from utils.cutting import catalog_cutting_fee

    order = _order_for_item(item)
    if order_money_locked(order):
        return

    snap = getattr(item, 'pricing_snapshot', None)
    if _line_variant_changed(item, snap):
        from models.product import Product
        product = product or Product.query.get(item.product_id)
        if product:
            snap = resnapshot_item_from_catalog(item, product, order)
            item.price_choice = None
    if not snap:
        from models.product import Product
        product = product or Product.query.get(item.product_id)
        snap = synthetic_snapshot_from_stored(item, product)
        item.pricing_snapshot = snap

    want_cut = bool(getattr(item, 'cutting', False))
    cannot = bool(getattr(item, 'cannot_fulfill', False))
    fee = getattr(item, 'cutting_fee', None)
    if want_cut and fee is None:
        from models.product import Product
        product = product or Product.query.get(item.product_id)
        fee = catalog_cutting_fee(product) if product else 0
    pooled = pooled_product_qty_for_item(item, product_qty)
    unit_price, total_price, fee_out = price_from_snapshot(
        snap,
        item.quantity,
        item.final_weight,
        product_qty=pooled,
        is_unavailable=item.is_unavailable,
        accept_substitute=item.accept_substitute,
        cannot_fulfill=cannot,
        cutting=want_cut,
        cutting_fee=fee,
    )
    if want_cut and not cannot:
        item.cutting_fee = fee_out
    elif not want_cut:
        item.cutting_fee = None
    item.unit_price = round_money(unit_price)
    item.total_price = round_money(total_price)


def combine_order_notes(orders):
    """Merge non-empty notes from multiple orders, deduped, separated by ---."""
    parts = []
    seen = set()
    for order in orders:
        if not getattr(order, 'notes', None):
            continue
        for chunk in str(order.notes).split('\n---\n'):
            text = chunk.strip()
            if text and text not in seen:
                seen.add(text)
                parts.append(text)
    return '\n---\n'.join(parts) if parts else None


def order_item_fields_for_merge(source_item):
    """Snapshot order line fields preserved when merging orders."""
    return {
        'product_id': source_item.product_id,
        'quantity': source_item.quantity,
        'unit_price': source_item.unit_price,
        'total_price': source_item.total_price,
        'final_weight': source_item.final_weight,
        'variant_id': source_item.variant_id,
        'variant_name': source_item.variant_name,
        'variant_price_delta': source_item.variant_price_delta,
        'cutting': bool(getattr(source_item, 'cutting', False)),
        'cutting_fee': getattr(source_item, 'cutting_fee', None),
        'accept_substitute': source_item.accept_substitute,
        'is_unavailable': source_item.is_unavailable,
        'cannot_fulfill': bool(getattr(source_item, 'cannot_fulfill', False)),
        'pricing_snapshot': getattr(source_item, 'pricing_snapshot', None),
        'price_choice': getattr(source_item, 'price_choice', None),
        'source_order_id': source_item.order_id,
        'source_item_id': source_item.id,
    }


def _resolve_item_on_sale(item, product, on_sale=None):
    """Deal sale is per group-deal product, not catalog-wide."""
    if on_sale is not None:
        return bool(on_sale)
    if not product:
        return False
    order = getattr(item, 'order', None)
    deal_id = getattr(order, 'group_deal_id', None) if order else None
    if not deal_id and getattr(item, 'order_id', None):
        from models.order import Order
        order = Order.query.get(item.order_id)
        deal_id = getattr(order, 'group_deal_id', None) if order else None
    if not deal_id:
        return False
    from models.groupdeal import GroupDealProduct
    dp = GroupDealProduct.query.filter_by(
        group_deal_id=deal_id,
        product_id=product.id,
    ).first()
    return bool(dp and dp.is_discount)


def _product_sale_fields(product, on_sale):
    prev = getattr(product, '_deal_is_discount', None)
    product._deal_is_discount = bool(on_sale)
    try:
        display = product.get_display_price()
        original = product.get_original_price()
    finally:
        if prev is None:
            if hasattr(product, '_deal_is_discount'):
                delattr(product, '_deal_is_discount')
        else:
            product._deal_is_discount = prev
    return {
        'is_discount': bool(on_sale),
        'price': display,
        'display_price': display,
        'original_price': original if on_sale else None,
        'sale_price': display if on_sale else None,
    }


def _relation_loaded(obj, name):
    """True when the relationship is already populated. Does not lazy-load."""
    from sqlalchemy import inspect
    return name not in inspect(obj).unloaded


def _deal_sale_by_item(items):
    """Batch (deal_id, product_id) → is_discount for a set of order lines."""
    from models.groupdeal import GroupDealProduct
    from models.order import Order
    from utils.query_batch import rows_by_id, unique_ids

    orders = {}
    missing_ids = []
    for item in items:
        order_id = getattr(item, 'order_id', None)
        if not order_id or order_id in orders:
            continue
        if _relation_loaded(item, 'order') and item.order is not None:
            orders[order_id] = item.order
        else:
            missing_ids.append(order_id)
    if missing_ids:
        orders.update(rows_by_id(Order, [oid for oid in missing_ids if oid not in orders]))

    deal_ids = []
    product_ids = []
    for item in items:
        order = orders.get(getattr(item, 'order_id', None))
        deal_id = getattr(order, 'group_deal_id', None) if order else None
        if deal_id and item.product_id:
            deal_ids.append(deal_id)
            product_ids.append(item.product_id)

    sale_map = {}
    deal_ids = unique_ids(deal_ids)
    product_ids = unique_ids(product_ids)
    if deal_ids and product_ids:
        for dp in GroupDealProduct.query.filter(
            GroupDealProduct.group_deal_id.in_(deal_ids),
            GroupDealProduct.product_id.in_(product_ids),
        ).all():
            sale_map[(dp.group_deal_id, dp.product_id)] = bool(dp.is_discount)

    on_sale_by_item = {}
    for item in items:
        order = orders.get(getattr(item, 'order_id', None))
        deal_id = getattr(order, 'group_deal_id', None) if order else None
        on_sale_by_item[id(item)] = bool(
            sale_map.get((deal_id, item.product_id))
        ) if deal_id else False
    return on_sale_by_item


def enrich_order_item_dict(item, product=None, source_order=None, on_sale=None):
    """Add display fields for API responses."""
    from models.product import Product

    product = product or Product.query.get(item.product_id)
    item_dict = item.to_dict()

    is_unavailable = bool(item.is_unavailable)
    accept_sub = item.accept_substitute
    is_substituted = is_unavailable and accept_sub is True and product and product.substitute_enabled
    is_declined_substitute = is_unavailable and accept_sub is False
    is_pending_substitute = is_unavailable and accept_sub is None
    # Legacy field — lines are never auto-removed; admin deletes manually if needed.
    is_struck_out = False

    if product:
        raw_images = product.images if product.images and isinstance(product.images, list) else []
        if not raw_images and product.image:
            raw_images = [product.image]
        images = public_image_urls(raw_images)
        thumbs = thumbnail_urls(raw_images)
        on_sale = _resolve_item_on_sale(item, product, on_sale)
        item_dict['product'] = {
            'id': product.id,
            'name': product.name,
            'image': images[0] if images else public_image_url(product.image),
            'image_thumb': thumbs[0] if thumbs else thumbnail_url(product.image),
            'images': images,
            'image_thumbs': thumbs,
            'description': product.description,
            'pricing_type': product.pricing_type,
            'pricing_data': product.pricing_data,
            'substitute_enabled': product.substitute_enabled,
            'substitute': product.get_substitute_dict(),
            'variants': [v.to_dict() for v in product.get_active_variants()],
            'cutting_enabled': bool(getattr(product, 'cutting_enabled', False)),
            'cutting_fee': float(product.cutting_fee) if getattr(product, 'cutting_fee', None) is not None else 0.0,
            **_product_sale_fields(product, on_sale),
        }

    if item.variant_id or item.variant_name:
        item_dict['variant'] = {
            'id': item.variant_id,
            'name': item.variant_name,
            'price_delta': float(item.variant_price_delta) if item.variant_price_delta is not None else 0,
        }

    if getattr(item, 'source_order_id', None) or getattr(item, 'source_item_id', None):
        src_order = source_order
        if src_order is None and item.source_order_id:
            src_order = item.source_order
        item_dict['lineage'] = {
            'source_order_id': item.source_order_id,
            'source_order_number': src_order.order_number if src_order else None,
            'source_item_id': item.source_item_id,
        }

    if is_substituted and product:
        sub = product.get_substitute_dict() or {}
        item_dict['display_name'] = sub.get('name') or product.name
        item_dict['display_images'] = sub.get('images') or []
    else:
        name = product.name if product else ''
        if item.variant_name:
            name = f'{name} ({item.variant_name})'
        if getattr(item, 'cutting', False):
            name = f'{name} · 切分' if name else '切分'
        item_dict['display_name'] = name
        if product:
            imgs = product.images if product.images and isinstance(product.images, list) else []
            if not imgs and product.image:
                imgs = [product.image]
            item_dict['display_images'] = public_image_urls(imgs)

    item_dict['is_substituted'] = is_substituted
    item_dict['is_struck_out'] = is_struck_out
    item_dict['is_declined_substitute'] = is_declined_substitute
    item_dict['is_pending_substitute'] = is_pending_substitute
    if product and product.substitute_enabled and accept_sub is not None:
        item_dict['substitute_preference_label'] = (
            '接受备选' if accept_sub is True else '不要备选'
        )
    if getattr(item, 'price_choice', None) == 'locked_old' and product:
        quote = quote_catalog_line(product, item)
        if quote is not None and round_money(quote['total_price']) == round_money(item.total_price):
            item.price_choice = None
            item_dict['price_choice'] = None
        elif quote is not None:
            item_dict['catalog_unit_price'] = quote['unit_price']
            item_dict['catalog_total_price'] = quote['total_price']
    return item_dict


def clear_locked_price_choices_matching_catalog(product):
    """Drop locked_old once the catalog price is back to what the line charges."""
    if product is None or not getattr(product, 'id', None):
        return
    lines = OrderItem.query.filter(
        OrderItem.product_id == product.id,
        OrderItem.price_choice == 'locked_old',
        OrderItem.active(),
    ).all()
    for line in lines:
        quote = quote_catalog_line(product, line)
        if quote is not None and round_money(quote['total_price']) == round_money(line.total_price):
            line.price_choice = None


def quote_catalog_line(product, item):
    """What this line would cost on the current catalog. None when it cannot be priced."""
    order = _order_for_item(item)
    from utils.influencer_pricing import attach_influencer_buyer_discount
    attach_deal_sale(product, group_deal_id=getattr(order, 'group_deal_id', None))
    attach_influencer_buyer_discount(product, getattr(order, 'user_id', None))
    try:
        return build_priced_order_item(
            product,
            quantity=item.quantity,
            final_weight=item.final_weight,
            variant_id=item.variant_id,
            accept_substitute=item.accept_substitute,
            cutting=bool(getattr(item, 'cutting', False)),
            is_unavailable=bool(item.is_unavailable),
            cannot_fulfill=bool(getattr(item, 'cannot_fulfill', False)),
            require_variant=False,
            product_qty=pooled_product_qty_for_item(item, None),
        )
    except ValueError:
        return None


def buyer_pricing_dict(user, product_ids):
    """Rates for live JS estimate (admin/order edit). Empty when not 推荐官."""
    from services.influencer_service import resolve_rates_for_products

    if not user or not getattr(user, 'is_influencer', False):
        return {'influencer': False, 'rates': {}}
    ids = []
    seen = set()
    for raw in product_ids or []:
        if raw is None:
            continue
        pid = int(raw)
        if pid in seen:
            continue
        seen.add(pid)
        ids.append(pid)
    rates = {}
    if ids:
        resolved = resolve_rates_for_products(user.id, ids)
        for pid, pair in (resolved or {}).items():
            if not pair:
                continue
            commission_type, amount = pair
            amount_f = float(amount or 0)
            if amount_f <= 0:
                continue
            rates[str(pid)] = {
                'commission_type': commission_type,
                'amount': amount_f,
            }
    return {'influencer': True, 'rates': rates}


def enrich_order_items(items):
    """Serialize many order lines with one product/source-order prefetch.

    Reuses relationships already eager-loaded on the lines. Missing products,
    source orders, and deal-sale flags are loaded once for the whole set, so
    callers can pass every line from a page instead of one order at a time.
    """
    from models.order import Order
    from utils.query_batch import products_by_ids, rows_by_id

    items = list(items or [])
    if not items:
        return []

    products = {}
    missing_product_ids = []
    source_orders = {}
    missing_source_ids = []
    for item in items:
        product_id = item.product_id
        if product_id and product_id not in products:
            loaded_product = item.product if _relation_loaded(item, 'product') else None
            if loaded_product is not None and _relation_loaded(loaded_product, 'variants'):
                products[product_id] = loaded_product
            else:
                missing_product_ids.append(product_id)
        if item.source_order_id and item.source_order_id not in source_orders:
            if _relation_loaded(item, 'source_order'):
                if item.source_order is not None:
                    source_orders[item.source_order_id] = item.source_order
            else:
                missing_source_ids.append(item.source_order_id)

    if missing_product_ids:
        products.update(products_by_ids(missing_product_ids))
    if missing_source_ids:
        source_orders.update(rows_by_id(Order, missing_source_ids))
    on_sale_by_item = _deal_sale_by_item(items)
    payloads = [
        enrich_order_item_dict(
            item,
            products.get(item.product_id),
            source_order=source_orders.get(item.source_order_id) if item.source_order_id else None,
            on_sale=on_sale_by_item.get(id(item), False),
        )
        for item in items
    ]
    _commit_released_price_choices(items)
    return payloads


def _commit_released_price_choices(items):
    """Persist locked_old clears from a read, when this request has no other edits."""
    from models import db

    released = [
        item for item in items
        if item in db.session.dirty and getattr(item, 'price_choice', None) is None
    ]
    if not released:
        return
    extra = [obj for obj in db.session.dirty if obj not in released]
    if db.session.new or extra:
        return
    db.session.commit()


def bulk_set_product_fulfillment(group_deal_id, product_id, is_unavailable):
    """
    Mark all order lines for a product in a group deal unavailable/available.
    Applies substitute pricing or zero per each line's accept_substitute.
    Returns stats dict.
    """
    from models.order import Order
    from models import db
    from constants.status_enums import OrderStatus
    from sqlalchemy.orm import selectinload

    product = Product.query.get(product_id)
    if not product:
        raise ValueError(f'Product {product_id} not found')
    if is_unavailable and not product.substitute_enabled:
        raise ValueError('此商品未配置备选，无法切换备选')

    orders = Order.query.options(selectinload(Order.items)).filter(
        Order.group_deal_id == group_deal_id,
        Order.deleted_at.is_(None),
        Order.status != OrderStatus.CANCELLED.value,
    ).all()

    stats = {
        'items_updated': 0,
        'orders_updated': 0,
        'will_substitute': 0,
        'will_pending': 0,
        'restored': 0,
    }

    from utils.order_lock import order_money_locked

    for order in orders:
        if order_money_locked(order):
            continue
        order_changed = False
        for item in order.items:
            if item.product_id != product_id:
                continue
            if bool(item.is_unavailable) == bool(is_unavailable):
                continue
            item.is_unavailable = bool(is_unavailable)
            stats['items_updated'] += 1
            order_changed = True
            if is_unavailable:
                if item.accept_substitute is True and product.substitute_enabled:
                    stats['will_substitute'] += 1
                else:
                    stats['will_pending'] += 1
            else:
                stats['restored'] += 1
        if order_changed:
            from utils.order_totals import sync_order_pricing
            sync_order_pricing(order, reprice_lines=True)
            stats['orders_updated'] += 1

    db.session.commit()
    return stats


def restore_existing_line_weights(request_items, existing_items):
    """Customers cannot set final_weight. Keep staff-entered weights on unchanged lines."""
    existing = {item.id: item for item in (existing_items or []) if getattr(item, 'id', None)}
    for item_data in request_items or []:
        item_data.pop('final_weight', None)
        src = existing.get(item_data.get('id'))
        if not src or src.final_weight is None:
            continue
        if src.product_id != item_data.get('product_id'):
            continue
        if int(src.quantity or 0) != int(item_data.get('quantity') or 0):
            continue
        if src.variant_id != item_data.get('variant_id'):
            continue
        if bool(getattr(src, 'cutting', False)) != bool(item_data.get('cutting')):
            continue
        item_data['final_weight'] = float(src.final_weight)
    return request_items


def priced_items_from_request(items, unavailable_by_item_id=None, *, require_variant=True, group_deal_id=None, buyer_user_id=None):
    """Build priced order line dicts from request items. Raises ValueError on error."""
    unavailable_by_item_id = unavailable_by_item_id or {}
    order_items = []
    subtotal = Decimal('0')
    from models.groupdeal import GroupDealProduct
    from models.user import User
    from sqlalchemy.orm import selectinload
    from utils.query_batch import products_by_ids
    from utils.influencer_pricing import attach_influencer_buyer_discount
    from services.influencer_service import resolve_rates_for_products

    products = products_by_ids(item_data.get('product_id') for item_data in items)
    expanded = expand_request_items(items, products=products)

    sale_by_product = {}
    if group_deal_id and products:
        sale_by_product = {
            dp.product_id: dp
            for dp in GroupDealProduct.query.filter(
                GroupDealProduct.group_deal_id == group_deal_id,
                GroupDealProduct.product_id.in_(list(products)),
            ).all()
        }

    buyer = None
    rate_by_product = {}
    if buyer_user_id:
        buyer = User.query.options(
            selectinload(User.roles),
            selectinload(User.influencer_profile),
        ).get(buyer_user_id)
        if buyer and buyer.is_influencer:
            rate_by_product = resolve_rates_for_products(buyer.id, list(products))

    for product in products.values():
        attach_deal_sale(product, deal_product=sale_by_product.get(product.id) if group_deal_id else None)
        attach_influencer_buyer_discount(
            product,
            user_id=buyer_user_id,
            user=buyer,
            resolved=rate_by_product.get(product.id) if buyer and buyer.is_influencer else None,
        )

    pooled_qty = {}
    for item_data in expanded:
        pid = item_data['product_id']
        pooled_qty[pid] = pooled_qty.get(pid, 0) + int(item_data.get('quantity') or 0)

    for item_data in expanded:
        product = products.get(item_data['product_id'])
        if not product:
            raise ValueError(f'Product {item_data["product_id"]} not found')

        item_id = item_data.get('id')
        is_unavailable = item_data.get('is_unavailable')
        if is_unavailable is None and item_id:
            is_unavailable = unavailable_by_item_id.get(item_id, False)
        else:
            is_unavailable = bool(is_unavailable)

        priced = build_priced_order_item(
            product=product,
            quantity=item_data['quantity'],
            pricing_type=item_data.get('pricing_type', product.pricing_type),
            final_weight=item_data.get('final_weight'),
            variant_id=item_data.get('variant_id'),
            accept_substitute=item_data.get('accept_substitute'),
            cutting=bool(item_data.get('cutting')),
            is_unavailable=is_unavailable,
            cannot_fulfill=bool(item_data.get('cannot_fulfill', False)),
            require_variant=require_variant,
            product_qty=pooled_qty.get(item_data['product_id']),
        )
        priced['_request_item_id'] = item_data.get('id')
        subtotal += round_money(priced['total_price'])
        order_items.append(priced)

    return order_items, subtotal


def create_order_item_rows(order_id, priced_items, db_session):
    for priced in priced_items:
        order_item = OrderItem(
            order_id=order_id,
            product_id=priced['product_id'],
            quantity=priced['quantity'],
            unit_price=round_money(priced['unit_price']),
            total_price=round_money(priced['total_price']),
            final_weight=priced.get('final_weight'),
            variant_id=priced.get('variant_id'),
            variant_name=priced.get('variant_name'),
            variant_price_delta=priced.get('variant_price_delta'),
            cutting=bool(priced.get('cutting')),
            cutting_fee=priced.get('cutting_fee'),
            accept_substitute=priced.get('accept_substitute'),
            is_unavailable=priced.get('is_unavailable', False),
            cannot_fulfill=priced.get('cannot_fulfill', False),
            pricing_snapshot=priced.get('pricing_snapshot'),
            price_choice=priced.get('price_choice'),
            source_order_id=priced.get('source_order_id'),
            source_item_id=priced.get('source_item_id'),
        )
        db_session.add(order_item)


def apply_product_substitute_fields(product, data):
    """Apply substitute config from validated product payload."""
    if 'substitute_enabled' not in data:
        return
    product.substitute_enabled = bool(data.get('substitute_enabled'))
    if product.substitute_enabled:
        product.substitute_name = data.get('substitute_name')
        product.substitute_description = data.get('substitute_description')
        product.substitute_images = data.get('substitute_images')
        product.substitute_pricing_type = data.get('substitute_pricing_type') or data.get('pricing_type')
        product.substitute_pricing_data = data.get('substitute_pricing_data')
        # Keep legacy column in sync for per_item
        if product.substitute_pricing_type == 'per_item' and product.substitute_pricing_data:
            product.substitute_price = product.substitute_pricing_data.get('price')
        else:
            product.substitute_price = None
    else:
        product.substitute_name = None
        product.substitute_description = None
        product.substitute_images = None
        product.substitute_price = None
        product.substitute_pricing_type = None
        product.substitute_pricing_data = None


def apply_product_cutting_fields(product, data):
    """Apply 切分 config from validated product payload."""
    if 'cutting_enabled' in data:
        product.cutting_enabled = bool(data.get('cutting_enabled'))
    if 'cutting_fee' in data and data.get('cutting_fee') is not None:
        product.cutting_fee = data.get('cutting_fee') or 0
    if not product.cutting_enabled:
        product.cutting_fee = product.cutting_fee or 0


def sync_product_variants(product, variants_data):
    """Replace product variants from admin payload list."""
    from models import db

    if variants_data is None:
        return

    existing = {v.id: v for v in (product.variants or [])}
    keep_ids = set()

    for idx, row in enumerate(variants_data):
        vid = row.get('id')
        name = (row.get('name') or '').strip()
        if not name:
            continue
        price_delta = row.get('price_delta', 0)
        sort_order = row.get('sort_order', idx)
        is_active = row.get('is_active', True)
        price = row.get('price')
        sale_price = row.get('sale_price')
        quantity_breaks = normalize_quantity_breaks(row.get('quantity_breaks')) or None

        if vid and vid in existing:
            v = existing[vid]
            v.name = name
            v.price_delta = price_delta
            v.price = price
            v.sale_price = sale_price
            v.quantity_breaks = quantity_breaks
            v.sort_order = sort_order
            v.is_active = is_active
            keep_ids.add(vid)
        else:
            v = ProductVariant(
                product_id=product.id,
                name=name,
                price_delta=price_delta,
                price=price,
                sale_price=sale_price,
                quantity_breaks=quantity_breaks,
                sort_order=sort_order,
                is_active=is_active,
            )
            db.session.add(v)
            db.session.flush()
            keep_ids.add(v.id)

    for vid, v in list(existing.items()):
        if vid not in keep_ids:
            db.session.delete(v)


def _same_line_identity(src, priced):
    if src.product_id != priced.get('product_id'):
        return False
    if src.variant_id != priced.get('variant_id'):
        return False
    return True


def preserve_existing_line_prices(priced_items, existing_items):
    """Keep the saved schedule when an edit does not change product or variant."""
    from collections import defaultdict
    existing_by_id = {item.id: item for item in (existing_items or []) if getattr(item, 'id', None)}
    pools = defaultdict(int)
    for priced in priced_items or []:
        pools[priced.get('product_id')] += int(priced.get('quantity') or 0)
    for priced in priced_items or []:
        src = existing_by_id.get(priced.get('_request_item_id'))
        if not src or not _same_line_identity(src, priced):
            continue
        snap = getattr(src, 'pricing_snapshot', None)
        if not snap:
            snap = synthetic_snapshot_from_stored(src, None)
        cutting = bool(priced.get('cutting'))
        fee = src.cutting_fee if cutting and bool(getattr(src, 'cutting', False)) else priced.get('cutting_fee')
        unit, total, fee_out = price_from_snapshot(
            snap,
            priced.get('quantity'),
            priced.get('final_weight'),
            product_qty=pools.get(priced.get('product_id')),
            is_unavailable=priced.get('is_unavailable'),
            accept_substitute=priced.get('accept_substitute'),
            cannot_fulfill=priced.get('cannot_fulfill'),
            cutting=cutting,
            cutting_fee=fee,
        )
        priced['unit_price'] = unit
        priced['total_price'] = total
        priced['pricing_snapshot'] = snap
        priced['price_choice'] = getattr(src, 'price_choice', None)
        priced['cutting_fee'] = fee_out if cutting else None


def _money_equal(left, right):
    return round_money(left or 0) == round_money(right or 0)


def backfill_pricing_snapshots():
    """Fill pricing_snapshot from the price already stored on each line. Does not change totals."""
    from models import db
    from models.order import Order, OrderItem
    from models.product import Product
    from utils.influencer_pricing import attach_influencer_buyer_discount
    from utils.query_batch import products_by_ids

    # JSON null and SQL NULL both load as None. SQLite does not match JSON null with IS NULL.
    items = [item for item in OrderItem.query.all() if not item.pricing_snapshot]
    if not items:
        return 0
    products = products_by_ids(item.product_id for item in items)
    order_ids = {item.order_id for item in items if item.order_id}
    orders = {
        order.id: order
        for order in Order.query.filter(Order.id.in_(order_ids)).all()
    } if order_ids else {}
    filled = 0
    for item in items:
        product = products.get(item.product_id)
        order = orders.get(item.order_id)
        snap = None
        if product:
            attach_deal_sale(product, group_deal_id=getattr(order, 'group_deal_id', None))
            attach_influencer_buyer_discount(product, getattr(order, 'user_id', None))
            try:
                quoted = build_priced_order_item(
                    product,
                    quantity=item.quantity,
                    final_weight=item.final_weight,
                    variant_id=item.variant_id,
                    accept_substitute=item.accept_substitute,
                    cutting=bool(item.cutting),
                    is_unavailable=bool(item.is_unavailable),
                    cannot_fulfill=bool(item.cannot_fulfill),
                    require_variant=False,
                )
            except ValueError:
                quoted = None
            if (
                quoted
                and _money_equal(quoted['unit_price'], item.unit_price)
                and _money_equal(quoted['total_price'], item.total_price)
            ):
                snap = quoted['pricing_snapshot']
        if snap is None:
            snap = synthetic_snapshot_from_stored(item, product)
        item.pricing_snapshot = snap
        filled += 1
    db.session.flush()
    return filled
