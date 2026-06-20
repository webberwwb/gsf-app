"""Item replace must recalculate order.subtotal from active lines."""
from datetime import datetime
from decimal import Decimal

from models import db
from models.order import Order, OrderItem
from models.product import Product
from models.user import User
from models.groupdeal import GroupDeal
from constants.status_enums import UserStatus
from utils.order_totals import recalculate_order_totals
from utils.order_audit import active_items_for_order


def test_recalculate_uses_active_items_only(app, db_session):
    user = User(phone='9999990001', nickname='Recalc Test', status=UserStatus.ACTIVE.value)
    db_session.add(user)
    db_session.flush()

    p1 = Product(name='P1', pricing_type='per_item', pricing_data={'price': 11}, is_active=True)
    p2 = Product(name='P2', pricing_type='per_item', pricing_data={'price': 10}, is_active=True)
    db_session.add_all([p1, p2])
    db_session.flush()

    deal = GroupDeal(
        title='Test Deal',
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
        order_number='TEST-RECALC-001',
        subtotal=Decimal('0'),
        tax=Decimal('0'),
        shipping_fee=Decimal('0'),
        total=Decimal('0'),
        adjustment_amount=Decimal('0'),
        points_earned=0,
        delivery_method='pickup',
        payment_method='cash',
        payment_status='unpaid',
        status='submitted',
        store_credit_applied=Decimal('0'),
    )
    db_session.add(order)
    db_session.flush()

    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=p1.id,
            quantity=1,
            unit_price=Decimal('22'),
            total_price=Decimal('22'),
        )
    )
    db_session.flush()

    recalculate_order_totals(order)
    assert order.subtotal == Decimal('22.00')

    OrderItem.soft_delete_for_order(order.id, db_session)
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=p1.id,
            quantity=2,
            unit_price=Decimal('11'),
            total_price=Decimal('22'),
        )
    )
    db_session.add(
        OrderItem(
            order_id=order.id,
            product_id=p2.id,
            quantity=1,
            unit_price=Decimal('10'),
            total_price=Decimal('10'),
        )
    )
    db_session.flush()

    recalculate_order_totals(order)
    active_sum = sum(i.total_price for i in active_items_for_order(order.id))
    assert order.subtotal == Decimal('32.00')
    assert active_sum == Decimal('32.00')
