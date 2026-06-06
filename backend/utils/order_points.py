"""Order loyalty points. See order_business_rules.ORDER_PRICING_AND_POINTS_RULES."""

from decimal import Decimal

from utils.order_business_rules import ORDER_PRICING_AND_POINTS_RULES
from utils.money import round_money


def calculate_order_points(order) -> int:
    """
    Points in cents: 1 point = $0.01 of product paid after credit and admin discount.
    Excludes shipping and credit-covered amounts. Admin discounts (negative
    adjustment) reduce points; surcharges (positive adjustment) do not add points.
    """
    subtotal = Decimal(str(order.subtotal or 0))
    credit = Decimal(str(order.store_credit_applied or 0))
    adjustment = Decimal(str(order.adjustment_amount or 0))
    discount = min(adjustment, Decimal('0'))
    dollars = round_money(max(Decimal('0'), subtotal - credit + discount))
    return int(dollars * 100)


def award_order_points(order, user):
    """Set order.points_earned and add to user.points balance (once per order)."""
    points = calculate_order_points(order)
    order.points_earned = points
    if user is not None and order.payment_date is None:
        user.points = (user.points or 0) + points
    return points


def revoke_order_points(order, user):
    """Remove previously credited points when marking paid → unpaid."""
    credited = order.points_earned or 0
    if user is not None and credited > 0 and order.payment_date is not None:
        user.points = max(0, (user.points or 0) - credited)
    order.payment_date = None
    order.points_earned = calculate_order_points(order)
    return credited


__doc__ = (calculate_order_points.__doc__ or '') + '\n\n' + ORDER_PRICING_AND_POINTS_RULES
