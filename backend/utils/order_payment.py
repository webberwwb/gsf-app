"""Mark an order paid and award points (cash, EMT, or Stripe)."""

from models.base import utc_now
from models.user import User
from constants.status_enums import PaymentStatus, OrderStatus, DeliveryMethod, PaymentMethod
from utils.order_points import award_order_points
from services import referral_service, influencer_service


def order_was_delivered(order):
    """True after the driver marked 已送达 (or the order already completed)."""
    if getattr(order, 'delivered_at', None):
        return True
    return getattr(order, 'status', None) in (
        OrderStatus.DELIVERED.value,
        OrderStatus.COMPLETED.value,
    )


def maybe_complete_order(order):
    """Complete only when payment is in and fulfillment is done.

    Delivery: 已送达 + paid (cash received or already paid online).
    Pickup: paid is enough (existing checkout / counter flow).
    """
    if getattr(order, 'payment_status', None) != PaymentStatus.PAID.value:
        return False
    if getattr(order, 'delivery_method', None) == DeliveryMethod.DELIVERY.value:
        if not order_was_delivered(order):
            return False
    order.status = OrderStatus.COMPLETED.value
    return True


def mark_order_paid(order, transaction_id=None, amount_charged=None):
    """Flip unpaid → paid and award points. Completes only when also fulfilled."""
    old_status = order.status
    if order.payment_status != PaymentStatus.PAID.value:
        user = User.query.get(order.user_id)
        award_order_points(order, user)
        order.payment_status = PaymentStatus.PAID.value
        order.payment_date = utc_now()
        maybe_complete_order(order)
    if transaction_id:
        order.payment_transaction_id = transaction_id
    if amount_charged is not None:
        order.stripe_amount_charged = amount_charged
    referral_service.on_order_first_completed(order, old_status)
    influencer_service.accrue_for_order(order)
    return order


def payment_method_error(
    delivery_method,
    payment_method,
    user=None,
    require_card_on_file=True,
    online_payment_enabled=False,
    delivery_consented=False,
):
    """Return a Chinese error string if delivery/payment combo is invalid, else None.

    Delivery requires this-order 须知 consent and a card on file. Cash or card is
    then allowed; e-transfer is not. Pickup stays cash / e-transfer.
    """
    if delivery_method == DeliveryMethod.DELIVERY.value:
        if not delivery_consented:
            return '请先阅读并同意《配送须知》'
        if require_card_on_file and user is not None and not getattr(user, 'stripe_payment_method_id', None):
            return '请先绑定银行卡后再提交配送订单'
        if payment_method == PaymentMethod.ETRANSFER.value:
            return '配送订单请使用现金或在线支付'
        return None
    if payment_method == PaymentMethod.CARD.value:
        if not online_payment_enabled:
            return '本团购暂不支持在线支付'
        return '自取订单请使用现金或电子转账'
    return None


def copy_user_card_to_order(order, user):
    if not user:
        return
    order.stripe_customer_id = user.stripe_customer_id
    order.stripe_payment_method_id = user.stripe_payment_method_id
    order.stripe_card_brand = user.stripe_card_brand
    order.stripe_card_last4 = user.stripe_card_last4
    if user.stripe_payment_method_id and not order.stripe_charge_status:
        order.stripe_charge_status = 'setup_complete'


def stripe_order_bucket(order):
    """paid | failed | ready | no_card for card / Stripe admin dashboards."""
    if getattr(order, 'payment_status', None) == PaymentStatus.PAID.value:
        return 'paid'
    if getattr(order, 'stripe_charge_status', None) == 'failed':
        return 'failed'
    if getattr(order, 'stripe_payment_method_id', None) or getattr(order, 'stripe_charge_status', None) == 'setup_complete':
        return 'ready'
    return 'no_card'


def delivery_ship_blocked(order, new_status):
    """True if this delivery order cannot move to a ship/complete status while unpaid."""
    ship_statuses = {
        OrderStatus.OUT_FOR_DELIVERY.value,
        'delivering',
    }
    if new_status not in ship_statuses:
        return False
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        return False
    if getattr(order, 'payment_method', None) != PaymentMethod.CARD.value:
        return False
    return order.payment_status != PaymentStatus.PAID.value
