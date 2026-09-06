"""Payment method rules and mark-paid helper (no live Stripe)."""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from constants.status_enums import DeliveryMethod, PaymentMethod, PaymentStatus, OrderStatus, UserStatus
from models import db
from models.groupdeal import GroupDeal
from models.order import Order
from models.user import User
from utils.order_payment import (
    payment_method_error,
    delivery_ship_blocked,
    mark_order_paid,
    copy_user_card_to_order,
    stripe_order_bucket,
)


def test_delivery_requires_card():
    assert payment_method_error('delivery', 'etransfer', online_payment_enabled=True) == '配送订单必须使用信用卡支付'
    assert payment_method_error('delivery', 'cash', online_payment_enabled=True) == '配送订单必须使用信用卡支付'
    assert payment_method_error(
        'delivery', 'card', require_card_on_file=False, online_payment_enabled=True
    ) is None


def test_delivery_requires_card_on_file():
    user = SimpleNamespace(stripe_payment_method_id=None)
    assert payment_method_error(
        'delivery', 'card', user, online_payment_enabled=True
    ) == '请先绑定银行卡后再提交配送订单'
    user.stripe_payment_method_id = 'pm_test'
    assert payment_method_error('delivery', 'card', user, online_payment_enabled=True) is None


def test_pickup_rejects_card():
    assert payment_method_error('pickup', 'card', online_payment_enabled=True) == '自取订单请使用现金或电子转账'
    assert payment_method_error('pickup', 'cash', online_payment_enabled=True) is None
    assert payment_method_error('pickup', 'etransfer', online_payment_enabled=True) is None


def test_legacy_deal_rejects_card_allows_cash_delivery():
    assert payment_method_error('delivery', 'cash') is None
    assert payment_method_error('delivery', 'etransfer') is None
    assert payment_method_error('pickup', 'cash') is None
    assert payment_method_error('delivery', 'card') == '本团购暂不支持在线支付'
    assert payment_method_error('pickup', 'card') == '本团购暂不支持在线支付'


def test_delivery_ship_blocked_while_unpaid():
    order = SimpleNamespace(
        delivery_method=DeliveryMethod.DELIVERY.value,
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.UNPAID.value,
    )
    assert delivery_ship_blocked(order, OrderStatus.OUT_FOR_DELIVERY.value) is True
    assert delivery_ship_blocked(order, 'delivering') is True
    assert delivery_ship_blocked(order, OrderStatus.PREPARING.value) is False
    order.payment_status = PaymentStatus.PAID.value
    assert delivery_ship_blocked(order, OrderStatus.OUT_FOR_DELIVERY.value) is False


def test_delivery_cash_not_ship_blocked():
    order = SimpleNamespace(
        delivery_method=DeliveryMethod.DELIVERY.value,
        payment_method=PaymentMethod.CASH.value,
        payment_status=PaymentStatus.UNPAID.value,
    )
    assert delivery_ship_blocked(order, OrderStatus.OUT_FOR_DELIVERY.value) is False


def test_pickup_never_ship_blocked():
    order = SimpleNamespace(
        delivery_method=DeliveryMethod.PICKUP.value,
        payment_status=PaymentStatus.UNPAID.value,
    )
    assert delivery_ship_blocked(order, OrderStatus.OUT_FOR_DELIVERY.value) is False


def test_copy_user_card_to_order():
    user = SimpleNamespace(
        stripe_customer_id='cus_1',
        stripe_payment_method_id='pm_1',
        stripe_card_brand='visa',
        stripe_card_last4='4242',
    )
    order = SimpleNamespace(
        stripe_customer_id=None,
        stripe_payment_method_id=None,
        stripe_card_brand=None,
        stripe_card_last4=None,
        stripe_charge_status=None,
    )
    copy_user_card_to_order(order, user)
    assert order.stripe_customer_id == 'cus_1'
    assert order.stripe_payment_method_id == 'pm_1'
    assert order.stripe_card_brand == 'visa'
    assert order.stripe_card_last4 == '4242'
    assert order.stripe_charge_status == 'setup_complete'


def test_stripe_order_bucket():
    assert stripe_order_bucket(SimpleNamespace(
        payment_status=PaymentStatus.PAID.value,
        stripe_charge_status='failed',
        stripe_payment_method_id='pm_1',
    )) == 'paid'
    assert stripe_order_bucket(SimpleNamespace(
        payment_status=PaymentStatus.UNPAID.value,
        stripe_charge_status='failed',
        stripe_payment_method_id='pm_1',
    )) == 'failed'
    assert stripe_order_bucket(SimpleNamespace(
        payment_status=PaymentStatus.UNPAID.value,
        stripe_charge_status='setup_complete',
        stripe_payment_method_id='pm_1',
    )) == 'ready'
    assert stripe_order_bucket(SimpleNamespace(
        payment_status=PaymentStatus.UNPAID.value,
        stripe_charge_status=None,
        stripe_payment_method_id=None,
    )) == 'no_card'


def test_mark_order_paid_awards_points_and_completes(app, db_session):
    user = User(phone='9999990002', nickname='Pay Test', status=UserStatus.ACTIVE.value, points=0)
    db_session.add(user)
    db_session.flush()

    deal = GroupDeal(
        title='Pay Deal',
        order_start_date=datetime(2026, 1, 1),
        order_end_date=datetime(2026, 12, 31),
        pickup_date=datetime(2026, 6, 1),
        status='active',
    )
    db_session.add(deal)
    db_session.flush()

    order = Order(
        user_id=user.id,
        group_deal_id=deal.id,
        order_number='TEST-PAY-001',
        subtotal=Decimal('20.00'),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal('20.00'),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method=DeliveryMethod.DELIVERY.value,
        payment_method=PaymentMethod.CARD.value,
        payment_status=PaymentStatus.UNPAID.value,
        status=OrderStatus.PREPARING.value,
        store_credit_applied=Decimal('0'),
    )
    db_session.add(order)
    db_session.flush()

    mark_order_paid(order, transaction_id='pi_test', amount_charged=Decimal('20.00'))
    db_session.flush()

    assert order.payment_status == PaymentStatus.PAID.value
    assert order.status == OrderStatus.COMPLETED.value
    assert order.payment_transaction_id == 'pi_test'
    assert order.stripe_amount_charged == Decimal('20.00')
    assert order.points_earned > 0
