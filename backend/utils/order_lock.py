"""Whether an order's charged amounts are frozen."""
from constants.status_enums import OrderStatus, PaymentStatus

CLOSED_DEAL_STATUSES = (
    'closed',
    'preparing',
    'ready_for_pickup',
    'completed',
)


def order_money_locked(order) -> bool:
    """Paid, completed, and cancelled orders keep every stored amount."""
    if order is None:
        return False
    status = getattr(order, 'status', None)
    if status in (OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value):
        return True
    return getattr(order, 'payment_status', None) == PaymentStatus.PAID.value


def deal_accepts_price_choice(group_deal, now=None) -> bool:
    """True while the deal is not yet 截单, so a price change can still be chosen per order."""
    if group_deal is None:
        return False
    if getattr(group_deal, 'status', None) in CLOSED_DEAL_STATUSES:
        return False
    from models.base import utc_now

    now = now or utc_now()
    end = getattr(group_deal, 'order_end_date', None)
    if end and end < now:
        return False
    return True
