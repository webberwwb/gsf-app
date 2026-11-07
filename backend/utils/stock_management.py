"""
Stock management for group deals.

`GroupDealProduct.deal_stock_limit` is the deal cap for the whole product
(admin-set). `variant_stock_limits` is an optional per-flavor cap on the same
deal, keyed by variant id. Neither column changes when customers order,
cancel, or edit. Available units are cap minus quantity already reserved on
non-cancelled orders. A flavor cap applies only to lines with that variant.
The product cap still applies to every line of the product.
"""

from collections import defaultdict

from flask import current_app
from sqlalchemy import func

from models import db
from models.groupdeal import GroupDealProduct


def _lock_deal_products(group_deal_id, product_ids):
    ids = list({int(pid) for pid in product_ids if pid is not None})
    if not ids:
        return {}
    rows = (
        db.session.query(GroupDealProduct)
        .filter(
            GroupDealProduct.group_deal_id == group_deal_id,
            GroupDealProduct.product_id.in_(ids),
        )
        .with_for_update()
        .all()
    )
    return {row.product_id: row for row in rows}


def reserved_qty_by_product(group_deal_id, product_ids=None):
    """Units already held by live (non-cancelled, non-deleted) orders."""
    from constants.status_enums import OrderStatus
    from models.order import Order, OrderItem

    query = (
        db.session.query(
            OrderItem.product_id,
            func.coalesce(func.sum(OrderItem.quantity), 0),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.group_deal_id == group_deal_id,
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
            OrderItem.active(),
        )
    )
    if product_ids is not None:
        ids = list({int(pid) for pid in product_ids if pid is not None})
        if not ids:
            return {}
        query = query.filter(OrderItem.product_id.in_(ids))
    query = query.group_by(OrderItem.product_id)
    return {int(pid): int(qty) for pid, qty in query.all()}


def reserved_qty_by_variant(group_deal_id, product_ids=None):
    """Units already held per (product_id, variant_id) on live orders."""
    from constants.status_enums import OrderStatus
    from models.order import Order, OrderItem

    query = (
        db.session.query(
            OrderItem.product_id,
            OrderItem.variant_id,
            func.coalesce(func.sum(OrderItem.quantity), 0),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.group_deal_id == group_deal_id,
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
            OrderItem.active(),
            OrderItem.variant_id.isnot(None),
        )
    )
    if product_ids is not None:
        ids = list({int(pid) for pid in product_ids if pid is not None})
        if not ids:
            return {}
        query = query.filter(OrderItem.product_id.in_(ids))
    query = query.group_by(OrderItem.product_id, OrderItem.variant_id)
    return {(int(pid), int(vid)): int(qty) for pid, vid, qty in query.all()}


def _variant_label(variant_id):
    from models.product_variant import ProductVariant
    row = ProductVariant.query.get(int(variant_id)) if variant_id else None
    return row.name if row and row.name else '该规格'


def remaining_stock(cap, reserved):
    if cap is None:
        return None
    return max(0, int(cap) - int(reserved or 0))


def _item_fields(item):
    if hasattr(item, 'product_id'):
        return item.product_id, getattr(item, 'variant_id', None), item.quantity
    return item.get('product_id'), item.get('variant_id'), item.get('quantity')


def qty_by_product(items):
    """Sum quantity per product_id. Weight/份 lines are multiple rows of qty 1."""
    totals = defaultdict(int)
    for item in items or []:
        pid, _vid, qty = _item_fields(item)
        if pid is None:
            continue
        totals[pid] += int(qty or 0)
    return totals


def qty_by_variant(items):
    """Sum quantity per (product_id, variant_id). Lines without a variant are skipped."""
    totals = defaultdict(int)
    for item in items or []:
        pid, vid, qty = _item_fields(item)
        if pid is None or vid is None:
            continue
        totals[(int(pid), int(vid))] += int(qty or 0)
    return totals


def normalize_variant_stock_limits(raw):
    """Store only non-negative integer caps, keyed by variant id string."""
    if not isinstance(raw, dict):
        return None
    out = {}
    for key, value in raw.items():
        if value is None or value == '':
            continue
        try:
            variant_id = int(key)
            cap = int(value)
        except (TypeError, ValueError):
            continue
        if variant_id < 1 or cap < 0:
            continue
        out[str(variant_id)] = cap
    return out or None


def variant_caps(deal_product):
    """{variant_id: cap} for flavors that have a limit. Missing means unlimited."""
    raw = getattr(deal_product, 'variant_stock_limits', None) if deal_product else None
    normalized = normalize_variant_stock_limits(raw)
    if not normalized:
        return {}
    return {int(variant_id): cap for variant_id, cap in normalized.items()}


def _check_variant_caps(deal_products, needed_variants, reserved_variants, old_variants=None):
    """Return an error string when a flavor cap would be exceeded."""
    replacing = old_variants is not None
    old_variants = old_variants or {}
    for (product_id, variant_id), new_qty in needed_variants.items():
        cap = variant_caps(deal_products.get(product_id)).get(int(variant_id))
        if cap is None:
            continue
        old_qty = old_variants.get((product_id, int(variant_id)), 0)
        if replacing and old_qty == new_qty:
            continue
        held = reserved_variants.get((product_id, int(variant_id)), 0)
        label = _variant_label(variant_id)
        if replacing:
            projected = held - old_qty + new_qty
            if projected > cap:
                available = remaining_stock(cap, held - old_qty)
                return f'库存不足。{label}当前库存: {available}，需要增加: {new_qty - old_qty}'
            continue
        available = remaining_stock(cap, held)
        if available < new_qty:
            return f'库存不足。{label}当前库存: {available}，需要: {new_qty}'
    return None


def check_and_reserve_stock(group_deal_id, items):
    """
    Reject if live reserved + this request would exceed the deal cap.

    Locks deal-product rows so concurrent checkouts serialize. The cap column
    is not written.
    """
    try:
        needed = qty_by_product(items)
        if not needed:
            return True, None

        deal_products = _lock_deal_products(group_deal_id, needed.keys())
        reserved = reserved_qty_by_product(group_deal_id, needed.keys())
        for product_id, quantity in needed.items():
            deal_product = deal_products.get(product_id)
            if not deal_product:
                return False, f'Product {product_id} not found in this group deal'

            cap = deal_product.deal_stock_limit
            if cap is None:
                continue
            held = reserved.get(product_id, 0)
            available = remaining_stock(cap, held)
            if available < quantity:
                return False, f'库存不足。商品当前库存: {available}，需要: {quantity}'
            current_app.logger.info(
                f'Reserved stock for product {product_id}: {quantity} units. '
                f'Remaining: {available - quantity} (cap {cap})'
            )

        variant_error = _check_variant_caps(
            deal_products,
            needed_variants=qty_by_variant(items),
            reserved_variants=reserved_qty_by_variant(group_deal_id, needed.keys()),
        )
        if variant_error:
            return False, variant_error

        return True, None

    except Exception as e:
        current_app.logger.error(f'Error checking/reserving stock: {e}', exc_info=True)
        raise


def restore_stock(group_deal_id, items):
    """Cancel / delete no longer writes the cap. Kept for existing callers."""
    return True


def get_available_stock(group_deal_id, product_id):
    """Remaining units (cap minus live reserved), or None if unlimited."""
    try:
        deal_product = GroupDealProduct.query.filter_by(
            group_deal_id=group_deal_id,
            product_id=product_id
        ).first()

        if not deal_product:
            return None
        if deal_product.deal_stock_limit is None:
            return None
        held = reserved_qty_by_product(group_deal_id, [product_id]).get(product_id, 0)
        return remaining_stock(deal_product.deal_stock_limit, held)

    except Exception as e:
        current_app.logger.error(f'Error getting available stock: {e}', exc_info=True)
        return None


def update_stock_after_order_modification(group_deal_id, old_items, new_items):
    """
    Check the projected live reserved after replacing old_items with new_items.

    `old_items` may already be counted in reserved (existing order) or not
    (helper tests). Projected = reserved - old + new.
    """
    try:
        old_quantities = qty_by_product(old_items)
        new_quantities = qty_by_product(new_items)
        all_product_ids = set(old_quantities.keys()) | set(new_quantities.keys())
        if not all_product_ids:
            return True, None

        deal_products = _lock_deal_products(group_deal_id, all_product_ids)
        reserved = reserved_qty_by_product(group_deal_id, all_product_ids)

        for product_id in all_product_ids:
            old_qty = old_quantities.get(product_id, 0)
            new_qty = new_quantities.get(product_id, 0)
            if old_qty == new_qty:
                continue

            deal_product = deal_products.get(product_id)
            if not deal_product:
                if new_qty > old_qty:
                    return False, f'Product {product_id} not found in this group deal'
                continue

            cap = deal_product.deal_stock_limit
            if cap is None:
                continue
            projected = reserved.get(product_id, 0) - old_qty + new_qty
            if projected > cap:
                available = remaining_stock(cap, reserved.get(product_id, 0) - old_qty)
                return False, (
                    f'库存不足。商品当前库存: {available}，需要增加: {new_qty - old_qty}'
                )
            current_app.logger.info(
                f'Updated stock for product {product_id}: net change {new_qty - old_qty}. '
                f'Remaining: {remaining_stock(cap, projected)} (cap {cap})'
            )

        variant_error = _check_variant_caps(
            deal_products,
            needed_variants=qty_by_variant(new_items),
            reserved_variants=reserved_qty_by_variant(group_deal_id, all_product_ids),
            old_variants=qty_by_variant(old_items),
        )
        if variant_error:
            return False, variant_error

        return True, None

    except Exception as e:
        current_app.logger.error(f'Error updating stock after order modification: {e}', exc_info=True)
        raise
