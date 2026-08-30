"""Order header totals: shipping tier base, amount_due, recalculation."""

from decimal import Decimal

from utils.order_business_rules import ORDER_PRICING_AND_POINTS_RULES
from utils.shipping import calculate_shipping_fee, shipping_tier_base_from_parts
from utils.order_points import calculate_order_points
from utils.money import round_money


def _dec(value) -> Decimal:
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def shipping_tier_base(order) -> Decimal:
    """Net base for delivery fee tiers (discount-only adjustment)."""
    return shipping_tier_base_from_parts(
        _dec(order.subtotal),
        _dec(order.store_credit_applied),
        _dec(order.adjustment_amount),
    )


def calculate_amount_due(order) -> Decimal:
    """Payable amount after credit, adjustment, and shipping."""
    subtotal = _dec(order.subtotal)
    credit = _dec(order.store_credit_applied)
    adjustment = _dec(order.adjustment_amount)
    shipping = _dec(order.shipping_fee)
    return round_money(max(Decimal('0'), subtotal - credit + adjustment + shipping))


def order_items_for_shipping(order):
    """Build order_items list for calculate_shipping_fee from active lines."""
    from utils.order_audit import active_items_for_order
    from models.product import Product

    items = []
    for oi in active_items_for_order(order.id):
        product = Product.query.get(oi.product_id)
        if product:
            items.append({
                'product': product,
                'total_price': float(oi.total_price or 0),
            })
    return items


def recalculate_order_totals(order):
    """
    Recompute subtotal, shipping, total, and points from line items.
    See order_business_rules.ORDER_PRICING_AND_POINTS_RULES.
    """
    from models.address import Address
    from utils.order_audit import active_items_for_order

    subtotal = Decimal('0')
    active_items = active_items_for_order(order.id)
    for oi in active_items:
        subtotal += round_money(oi.total_price)

    order.subtotal = round_money(subtotal)

    address = None
    if order.delivery_method == 'delivery' and order.address_id:
        address = Address.query.get(order.address_id)

    tier_base = shipping_tier_base(order)
    shipping_items = order_items_for_shipping(order)
    shipping_fee = calculate_shipping_fee(
        tier_base,
        order.delivery_method,
        address,
        shipping_items,
    )

    adjustment = round_money(order.adjustment_amount)
    order.tax = Decimal('0')
    order.shipping_fee = round_money(shipping_fee)
    order.total = round_money(subtotal + shipping_fee + adjustment)
    order.points_earned = calculate_order_points(order)


def clamp_store_credit(order):
    """Ensure store_credit_applied does not exceed amount due (incl. shipping/adj)."""
    due_before_credit = _dec(order.subtotal) + _dec(order.shipping_fee) + _dec(order.adjustment_amount)
    applied = _dec(order.store_credit_applied)
    if applied > due_before_credit:
        order.store_credit_applied = round_money(max(Decimal('0'), due_before_credit))


def sync_order_pricing(order, *, reprice_lines=True):
    """Single entry after line or header changes."""
    from utils.order_item_pricing import recalculate_existing_item
    from utils.order_audit import active_items_for_order

    if reprice_lines:
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in active_items_for_order(order.id):
            grouped[item.product_id].append(item)
        for items in grouped.values():
            pooled = sum(int(i.quantity or 0) for i in items)
            for item in items:
                recalculate_existing_item(item, product_qty=pooled)
    recalculate_order_totals(order)
    clamp_store_credit(order)
    recalculate_order_totals(order)


__doc__ = (recalculate_order_totals.__doc__ or '') + '\n\n' + ORDER_PRICING_AND_POINTS_RULES
