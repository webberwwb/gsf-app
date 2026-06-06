"""Shared order line pricing: base product price, variants, and substitute fulfillment."""
from decimal import Decimal
from utils.money import round_money, round_money_float
from models.product_variant import ProductVariant
from models.product import Product
from models.order import OrderItem


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


def expand_request_items(items):
    """Split weight-based lines so each physical item is quantity=1."""
    expanded = []
    for item_data in items:
        product = Product.query.get(item_data['product_id'])
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
    return compute_price_from_config(pricing_type, product.pricing_data, quantity, final_weight)


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


def resolve_variant(product, variant_id, *, required=True):
    """
    Validate variant selection. Returns (variant, error_message).
    variant is None if no active variants on product.
    When required=False (admin edits), lines may omit variant_id on variant products.
    """
    active = product.get_active_variants() if hasattr(product, 'get_active_variants') else [
        v for v in (product.variants or []) if v.is_active
    ]

    if not active:
        if variant_id:
            return None, f'Product {product.id} has no variants'
        return None, None

    if not variant_id:
        if required:
            return None, f'请为商品「{product.name}」选择选项'
        return None, None

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


def build_priced_order_item(
    product,
    quantity,
    pricing_type=None,
    final_weight=None,
    variant_id=None,
    accept_substitute=None,
    is_unavailable=False,
    cannot_fulfill=False,
    require_variant=True,
):
    """
    Build dict of order item fields with prices and snapshots.
    Raises ValueError on validation errors.
    """
    variant, err = resolve_variant(product, variant_id, required=require_variant)
    if err:
        raise ValueError(err)

    err = validate_substitute_preference(product, accept_substitute)
    if err:
        raise ValueError(err)

    pricing_type = pricing_type or product.pricing_type
    unit_price, base_total = compute_base_price(product, quantity, pricing_type, final_weight)

    variant_delta = float(variant.price_delta) if variant else 0
    unit_price, base_total = apply_variant_delta_safe(
        unit_price, base_total, variant_delta, pricing_type, quantity, final_weight, product
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
        'accept_substitute': accept_substitute if product.substitute_enabled else None,
        'is_unavailable': bool(is_unavailable),
        'cannot_fulfill': bool(cannot_fulfill),
    }


def recalculate_existing_item(item, product=None):
    """Recalculate prices for an existing OrderItem row."""
    from models.product import Product

    product = product or Product.query.get(item.product_id)
    if not product:
        return

    pricing_type = product.pricing_type
    unit_price, base_total = compute_base_price(
        product, item.quantity, pricing_type, item.final_weight
    )
    variant_delta = float(item.variant_price_delta or 0)
    unit_price, base_total = apply_variant_delta_safe(
        unit_price, base_total, variant_delta, pricing_type, item.quantity, item.final_weight, product
    )
    unit_price, total_price = apply_fulfillment_price(
        unit_price,
        base_total,
        item.quantity,
        product,
        item.is_unavailable,
        item.accept_substitute,
        final_weight=item.final_weight,
        pricing_type=pricing_type,
        cannot_fulfill=bool(getattr(item, 'cannot_fulfill', False)),
    )
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
        'accept_substitute': source_item.accept_substitute,
        'is_unavailable': source_item.is_unavailable,
        'cannot_fulfill': bool(getattr(source_item, 'cannot_fulfill', False)),
        'source_order_id': source_item.order_id,
        'source_item_id': source_item.id,
    }


def enrich_order_item_dict(item, product=None):
    """Add display fields for API responses."""
    from models.order import Order
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
        images = product.images if product.images and isinstance(product.images, list) else []
        if not images and product.image:
            images = [product.image]
        item_dict['product'] = {
            'id': product.id,
            'name': product.name,
            'image': images[0] if images else product.image,
            'images': images,
            'description': product.description,
            'pricing_type': product.pricing_type,
            'pricing_data': product.pricing_data,
            'substitute_enabled': product.substitute_enabled,
            'substitute': product.get_substitute_dict(),
            'variants': [v.to_dict() for v in product.get_active_variants()],
        }

    if item.variant_id or item.variant_name:
        item_dict['variant'] = {
            'id': item.variant_id,
            'name': item.variant_name,
            'price_delta': float(item.variant_price_delta) if item.variant_price_delta is not None else 0,
        }

    if getattr(item, 'source_order_id', None) or getattr(item, 'source_item_id', None):
        src_order = Order.query.get(item.source_order_id) if item.source_order_id else None
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
        item_dict['display_name'] = name
        if product:
            imgs = product.images if product.images and isinstance(product.images, list) else []
            if not imgs and product.image:
                imgs = [product.image]
            item_dict['display_images'] = imgs

    item_dict['is_substituted'] = is_substituted
    item_dict['is_struck_out'] = is_struck_out
    item_dict['is_declined_substitute'] = is_declined_substitute
    item_dict['is_pending_substitute'] = is_pending_substitute
    if product and product.substitute_enabled and accept_sub is not None:
        item_dict['substitute_preference_label'] = (
            '接受备选' if accept_sub is True else '不要备选'
        )
    return item_dict


def bulk_set_product_fulfillment(group_deal_id, product_id, is_unavailable):
    """
    Mark all order lines for a product in a group deal unavailable/available.
    Applies substitute pricing or zero per each line's accept_substitute.
    Returns stats dict.
    """
    from models.order import Order, OrderItem
    from models import db
    from constants.status_enums import OrderStatus

    product = Product.query.get(product_id)
    if not product:
        raise ValueError(f'Product {product_id} not found')
    if is_unavailable and not product.substitute_enabled:
        raise ValueError('此商品未配置备选，无法切换备选')

    orders = Order.query.filter(
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

    for order in orders:
        order_changed = False
        for item in order.items:
            if item.product_id != product_id:
                continue
            if bool(item.is_unavailable) == bool(is_unavailable):
                continue
            item.is_unavailable = bool(is_unavailable)
            recalculate_existing_item(item, product)
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
            from utils.order_totals import recalculate_order_totals
            recalculate_order_totals(order)
            stats['orders_updated'] += 1

    db.session.commit()
    return stats


def priced_items_from_request(items, unavailable_by_item_id=None, *, require_variant=True):
    """Build priced order line dicts from request items. Raises ValueError on error."""
    unavailable_by_item_id = unavailable_by_item_id or {}
    order_items = []
    subtotal = Decimal('0')

    for item_data in expand_request_items(items):
        product = Product.query.get(item_data['product_id'])
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
            is_unavailable=is_unavailable,
            cannot_fulfill=bool(item_data.get('cannot_fulfill', False)),
            require_variant=require_variant,
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
            accept_substitute=priced.get('accept_substitute'),
            is_unavailable=priced.get('is_unavailable', False),
            cannot_fulfill=priced.get('cannot_fulfill', False),
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

        if vid and vid in existing:
            v = existing[vid]
            v.name = name
            v.price_delta = price_delta
            v.sort_order = sort_order
            v.is_active = is_active
            keep_ids.add(vid)
        else:
            v = ProductVariant(
                product_id=product.id,
                name=name,
                price_delta=price_delta,
                sort_order=sort_order,
                is_active=is_active,
            )
            db.session.add(v)
            db.session.flush()
            keep_ids.add(v.id)

    for vid, v in list(existing.items()):
        if vid not in keep_ids:
            db.session.delete(v)
