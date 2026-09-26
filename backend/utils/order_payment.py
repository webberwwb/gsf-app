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

    Delivery requires this-order 须知 consent. Cash, e-transfer, and card are
    allowed; a card on file is required only for online (card) payment.
    Pickup stays cash / e-transfer.
    """
    if delivery_method == DeliveryMethod.DELIVERY.value:
        if not delivery_consented:
            return '请先阅读并同意《配送须知》'
        if payment_method == PaymentMethod.CARD.value:
            if require_card_on_file and user is not None and not getattr(user, 'stripe_payment_method_id', None):
                return '请先绑定银行卡后再使用在线支付'
        return None
    if payment_method == PaymentMethod.CARD.value:
        if not online_payment_enabled:
            return '本团购暂不支持在线支付'
        return '自取订单请使用现金或电子转账'
    return None


def order_payer(order):
    """Customer who owns the order. The saved card lives on this user."""
    user = getattr(order, 'user', None)
    if user is not None:
        return user
    user_id = getattr(order, 'user_id', None)
    if not user_id:
        return None
    return User.query.get(user_id)


def card_on_file_for_order(order):
    """Card bind status is the customer's saved card, shared by every order.

    Charge outcome (failed / succeeded / amount) stays on the order.
    `setup_complete` was an old per-order copy of "card bound" and is ignored.
    """
    user = order_payer(order)
    charge_status = getattr(order, 'stripe_charge_status', None)
    if charge_status == 'setup_complete':
        charge_status = None
    bound = bool(user and getattr(user, 'stripe_payment_method_id', None))
    if not bound:
        return {
            'has_card_on_file': False,
            'stripe_customer_id': None,
            'stripe_payment_method_id': None,
            'stripe_card_brand': None,
            'stripe_card_last4': None,
            'stripe_charge_status': charge_status,
        }
    return {
        'has_card_on_file': True,
        'stripe_customer_id': user.stripe_customer_id,
        'stripe_payment_method_id': user.stripe_payment_method_id,
        'stripe_card_brand': user.stripe_card_brand,
        'stripe_card_last4': user.stripe_card_last4,
        'stripe_charge_status': charge_status,
    }


def stripe_order_bucket(order):
    """paid | failed | ready | no_card for card / Stripe admin dashboards."""
    if getattr(order, 'payment_status', None) == PaymentStatus.PAID.value:
        return 'paid'
    if getattr(order, 'stripe_charge_status', None) == 'failed':
        return 'failed'
    if card_on_file_for_order(order)['has_card_on_file']:
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
