"""
Commission calculation utilities for SDR commission management.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from models import db
from models.sdr import SDR, CommissionRule, CommissionRecord, CommissionExcludedUser
from models.groupdeal import GroupDeal
from models.order import Order, OrderItem
from models.product import Product
from models.user import User
from constants.status_enums import OrderStatus, PaymentStatus
from utils.money import round_money


def is_order_eligible_for_commission(order: Order) -> bool:
    """Only paid, completed, non-deleted orders count toward commission."""
    return (
        order.deleted_at is None
        and order.status == OrderStatus.COMPLETED.value
        and order.payment_status == PaymentStatus.PAID.value
    )


def _order_status_label(status: Optional[str]) -> str:
    if not status:
        return ''
    try:
        return OrderStatus.get_label(OrderStatus(status))
    except ValueError:
        return status


def _payment_status_label(status: Optional[str]) -> str:
    if not status:
        return ''
    try:
        return PaymentStatus.get_label(PaymentStatus(status))
    except ValueError:
        return status


def get_order_ineligibility_reason(order: Order) -> Optional[str]:
    if order.deleted_at is not None:
        return '已删除'
    if order.status == OrderStatus.CANCELLED.value:
        return '已取消'
    if order.status != OrderStatus.COMPLETED.value:
        return _order_status_label(order.status) or '未完成'
    if order.payment_status != PaymentStatus.PAID.value:
        return _payment_status_label(order.payment_status) or '未付款'
    return None


def get_commission_excluded_user_ids() -> set:
    """Return user IDs whose orders are excluded from commission calculation."""
    rows = CommissionExcludedUser.query.with_entities(CommissionExcludedUser.user_id).all()
    return {row[0] for row in rows}


def is_user_excluded_from_commission(user_id: int, excluded_user_ids: Optional[set] = None) -> bool:
    if excluded_user_ids is None:
        excluded_user_ids = get_commission_excluded_user_ids()
    return user_id in excluded_user_ids


def get_quarter_datetime_range(year: int, quarter: int) -> Tuple[datetime, datetime]:
    quarter_start_month = (quarter - 1) * 3 + 1
    if quarter == 4:
        quarter_end_month = 12
        quarter_end_day = 31
    else:
        quarter_end_month = quarter_start_month + 2
        if quarter_end_month in [1, 3, 5, 7, 8, 10, 12]:
            quarter_end_day = 31
        elif quarter_end_month in [4, 6, 9, 11]:
            quarter_end_day = 30
        else:
            quarter_end_day = 28

    quarter_start = datetime(year, quarter_start_month, 1)
    quarter_end = datetime(year, quarter_end_month, quarter_end_day, 23, 59, 59)
    return quarter_start, quarter_end


def get_commission_adjustment_discount(order: Order) -> Decimal:
    """Manual discount magnitude (negative adjustments only; surcharges do not reduce commission)."""
    adjustment = Decimal(str(order.adjustment_amount or 0))
    return max(Decimal('0'), -adjustment)


def get_commission_net_product_amount(order: Order) -> Decimal:
    """Net product amount: 商品小计 - 手动调整(折扣) - 积分抵扣 (不计运费)."""
    subtotal = Decimal(str(order.subtotal or 0))
    credit = Decimal(str(order.store_credit_applied or 0))
    discount = get_commission_adjustment_discount(order)
    return max(Decimal('0'), subtotal - discount - credit)


def get_commission_order_amount(order: Order) -> float:
    """Product order amount used for commission context (excludes delivery/shipping fee)."""
    return float(round_money(get_commission_net_product_amount(order)))


def get_commission_adjustment_ratio(order: Order) -> Decimal:
    """
    Scale factor applied to per-item commission when credit or discounts reduce net product amount.
    Bonuses (positive adjustment) do not increase commission above 100%.
    """
    subtotal = Decimal(str(order.subtotal or 0))
    if subtotal <= 0:
        return Decimal('0')
    net = get_commission_net_product_amount(order)
    return min(Decimal('1'), net / subtotal)


def _build_order_summary(
    order: Order,
    products_cache: Dict[int, str],
    exclusion_note: Optional[str] = None,
) -> Dict:
    order_items_summary = []
    for item in order.items:
        if item.product_id not in products_cache:
            product = Product.query.get(item.product_id)
            products_cache[item.product_id] = product.name if product else f"Product {item.product_id}"

        order_items_summary.append({
            'product_id': item.product_id,
            'product_name': products_cache[item.product_id],
            'quantity': item.quantity,
            'weight': float(item.final_weight) if item.final_weight else None,
            'unit_price': float(item.unit_price) if item.unit_price else None,
            'subtotal': float(item.total_price) if item.total_price else None,
        })

    user = User.query.get(order.user_id)
    user_name = None
    user_wechat = None
    if user:
        user_name = user.nickname or user.wechat_nickname or user.phone or f"User {user.id}"
        user_wechat = user.wechat

    shipping_fee = float(order.shipping_fee) if order.shipping_fee else 0.0
    gross_subtotal = float(order.subtotal) if order.subtotal else 0.0
    adjustment_amount = float(order.adjustment_amount) if order.adjustment_amount else 0.0
    adjustment_discount = float(get_commission_adjustment_discount(order))
    store_credit_applied = float(order.store_credit_applied) if order.store_credit_applied else 0.0
    order_amount = get_commission_order_amount(order)
    commission_ratio = float(get_commission_adjustment_ratio(order))

    summary = {
        'order_id': order.id,
        'order_number': order.order_number,
        'user_id': order.user_id,
        'user_name': user_name,
        'user_wechat': user_wechat,
        'user_phone': user.phone if user else None,
        'user_source': user.user_source if user else None,
        'order_status': order.status,
        'order_status_label': _order_status_label(order.status),
        'payment_status': order.payment_status,
        'payment_status_label': _payment_status_label(order.payment_status),
        'gross_subtotal': gross_subtotal,
        'adjustment_amount': adjustment_amount,
        'adjustment_discount': adjustment_discount,
        'store_credit_applied': store_credit_applied,
        'order_amount': order_amount,
        'commission_ratio': commission_ratio,
        'shipping_fee': shipping_fee,
        'items': order_items_summary,
        'total': float(order.total) if order.total else 0.0,
    }
    if exclusion_note:
        summary['exclusion_note'] = exclusion_note
    ineligibility_reason = get_order_ineligibility_reason(order)
    if ineligibility_reason:
        summary['ineligibility_reason'] = ineligibility_reason
    return summary


def get_excluded_orders_for_quarter(year: int, quarter: int) -> Dict:
    """Return orders in the quarter whose users are on the commission exclusion list."""
    quarter_start, quarter_end = get_quarter_datetime_range(year, quarter)

    excluded_entries = CommissionExcludedUser.query.all()
    excluded_user_ids = {entry.user_id for entry in excluded_entries}
    exclusion_notes_by_user = {
        entry.user_id: entry.notes for entry in excluded_entries if entry.notes
    }

    if not excluded_user_ids:
        return {
            'group_deals': [],
            'total_excluded_orders': 0,
            'total_excluded_order_value': 0.0,
        }

    group_deals = GroupDeal.query.filter(
        GroupDeal.created_at >= quarter_start,
        GroupDeal.created_at <= quarter_end,
        GroupDeal.deleted_at.is_(None),
    ).order_by(GroupDeal.created_at.desc()).all()

    products_cache: Dict[int, str] = {}
    group_deals_data = []
    total_excluded_orders = 0
    total_excluded_order_value = Decimal('0')

    for group_deal in group_deals:
        orders = Order.query.filter(
            Order.group_deal_id == group_deal.id,
            Order.deleted_at.is_(None),
            Order.status == OrderStatus.COMPLETED.value,
            Order.payment_status == PaymentStatus.PAID.value,
            Order.user_id.in_(excluded_user_ids),
        ).all()

        if not orders:
            continue

        order_summaries = []
        deal_order_value = Decimal('0')
        for order in orders:
            exclusion_note = exclusion_notes_by_user.get(order.user_id)
            order_summaries.append(_build_order_summary(order, products_cache, exclusion_note))
            deal_order_value += get_commission_net_product_amount(order)

        total_excluded_orders += len(order_summaries)
        total_excluded_order_value += deal_order_value

        group_deals_data.append({
            'group_deal_id': group_deal.id,
            'group_deal_title': group_deal.title or f"团购 #{group_deal.id}",
            'group_deal_date': group_deal.created_at.isoformat() if group_deal.created_at else None,
            'orders': order_summaries,
            'order_count': len(order_summaries),
            'total_order_value': float(deal_order_value),
        })

    return {
        'group_deals': group_deals_data,
        'total_excluded_orders': total_excluded_orders,
        'total_excluded_order_value': float(total_excluded_order_value),
    }


def calculate_commission_for_group_deal(group_deal_id: int, recalculate: bool = False) -> Dict:
    """
    Calculate commissions for all SDRs for a given group deal.
    
    Args:
        group_deal_id: ID of the group deal
        recalculate: If True, delete existing records and recalculate
    
    Returns:
        Dict with commission records for each SDR
        {
            'success': True,
            'records': [commission_record_dict, ...],
            'total_commission': float
        }
    """
    # Get group deal
    group_deal = GroupDeal.query.get(group_deal_id)
    if not group_deal:
        return {'success': False, 'error': 'Group deal not found'}
    
    # Delete existing records if recalculate is True
    if recalculate:
        CommissionRecord.query.filter_by(group_deal_id=group_deal_id).delete()
        db.session.commit()
    
    # Get all active SDRs
    sdrs = SDR.query.filter_by(is_active=True).all()
    if not sdrs:
        return {'success': False, 'error': 'No active SDRs found'}
    
    # Only paid, completed orders count toward commission
    orders = Order.query.filter(
        Order.group_deal_id == group_deal_id,
        Order.deleted_at.is_(None),
        Order.status == OrderStatus.COMPLETED.value,
        Order.payment_status == PaymentStatus.PAID.value,
    ).all()

    if not orders:
        return {'success': True, 'records': [], 'total_commission': 0, 'message': 'No eligible orders found'}
    
    commission_records = []
    total_all_commission = Decimal('0')
    
    # Calculate commission for each SDR
    for sdr in sdrs:
        commission_data = calculate_sdr_commission(sdr, orders)
        
        # Only create record if there's commission to pay
        if commission_data['total_commission'] > 0:
            # Check if record already exists
            existing_record = CommissionRecord.query.filter_by(
                group_deal_id=group_deal_id,
                sdr_id=sdr.id
            ).first()
            
            if existing_record:
                # Update existing record
                existing_record.total_commission = commission_data['total_commission']
                existing_record.own_customer_commission = commission_data['own_customer_commission']
                existing_record.general_customer_commission = commission_data['general_customer_commission']
                existing_record.details = commission_data['details']
                record = existing_record
            else:
                # Create new record
                record = CommissionRecord(
                    group_deal_id=group_deal_id,
                    sdr_id=sdr.id,
                    total_commission=commission_data['total_commission'],
                    own_customer_commission=commission_data['own_customer_commission'],
                    general_customer_commission=commission_data['general_customer_commission'],
                    details=commission_data['details'],
                    payment_status='pending'
                )
                db.session.add(record)
            
            db.session.commit()
            commission_records.append(record.to_dict(include_relations=True))
            total_all_commission += commission_data['total_commission']
    
    return {
        'success': True,
        'records': commission_records,
        'total_commission': float(total_all_commission)
    }


def calculate_sdr_commission(sdr: SDR, orders: List[Order]) -> Dict:
    """
    Calculate commission for a specific SDR across multiple orders.
    
    Args:
        sdr: SDR object
        orders: List of Order objects
    
    Returns:
        Dict with commission breakdown
        {
            'total_commission': Decimal,
            'own_customer_commission': Decimal,
            'general_customer_commission': Decimal,
            'details': [product_breakdown, ...]
        }
    """
    # Get all commission rules for this SDR
    commission_rules = {
        rule.product_id: rule
        for rule in CommissionRule.query.filter_by(sdr_id=sdr.id, is_active=True).all()
    }
    
    # Track commission per product
    product_commissions = {}  # product_id -> commission data
    
    total_commission = Decimal('0')
    own_customer_commission = Decimal('0')
    general_customer_commission = Decimal('0')
    excluded_user_ids = get_commission_excluded_user_ids()
    
    # Process each order
    for order in orders:
        # Get user to check source
        user = User.query.get(order.user_id)
        if not user:
            continue
        
        if is_user_excluded_from_commission(user.id, excluded_user_ids):
            continue
        
        is_own_customer = (user.user_source == sdr.source_identifier)
        commission_ratio = get_commission_adjustment_ratio(order)
        if commission_ratio <= 0:
            continue

        # Process each order item
        for item in order.items:
            product = Product.query.get(item.product_id)
            if not product or item.product_id not in commission_rules:
                continue
            
            rule = commission_rules[item.product_id]
            
            # Calculate commission based on product type
            commission = calculate_item_commission(
                product=product,
                order_item=item,
                commission_rule=rule,
                is_own_customer=is_own_customer
            )
            commission = round_money(commission * commission_ratio)

            if commission > 0:
                # Track totals
                total_commission += commission
                if is_own_customer:
                    own_customer_commission += commission
                else:
                    general_customer_commission += commission
                
                # Track per product
                if item.product_id not in product_commissions:
                    product_commissions[item.product_id] = {
                        'product_id': item.product_id,
                        'product_name': product.name,
                        'pricing_type': product.pricing_type,
                        'commission_type': rule.commission_type,  # How commission is calculated
                        'own_quantity': 0,
                        'general_quantity': 0,
                        'own_weight': Decimal('0'),
                        'general_weight': Decimal('0'),
                        'own_commission': Decimal('0'),
                        'general_commission': Decimal('0'),
                        'total_commission': Decimal('0'),
                        'own_rate': float(rule.own_customer_amount),
                        'general_rate': float(rule.general_customer_amount)
                    }
                
                product_data = product_commissions[item.product_id]
                product_data['total_commission'] += commission
                
                if is_own_customer:
                    product_data['own_commission'] += commission
                    # Track based on commission_type, not product pricing_type
                    if rule.commission_type == 'per_weight':
                        # Weight-based commission
                        weight = item.final_weight if item.final_weight else Decimal('0')
                        product_data['own_weight'] += weight
                    else:
                        # Item-based commission
                        product_data['own_quantity'] += item.quantity
                else:
                    product_data['general_commission'] += commission
                    # Track based on commission_type, not product pricing_type
                    if rule.commission_type == 'per_weight':
                        # Weight-based commission
                        weight = item.final_weight if item.final_weight else Decimal('0')
                        product_data['general_weight'] += weight
                    else:
                        # Item-based commission
                        product_data['general_quantity'] += item.quantity
    
    # Convert Decimal to float for JSON serialization
    details = [
        {
            **data,
            'own_weight': float(data['own_weight']) if data['own_weight'] else None,
            'general_weight': float(data['general_weight']) if data['general_weight'] else None,
            'own_commission': float(data['own_commission']),
            'general_commission': float(data['general_commission']),
            'total_commission': float(data['total_commission'])
        }
        for data in product_commissions.values()
    ]
    
    return {
        'total_commission': total_commission,
        'own_customer_commission': own_customer_commission,
        'general_customer_commission': general_customer_commission,
        'details': details
    }


def calculate_item_commission(
    product: Product,
    order_item: OrderItem,
    commission_rule: CommissionRule,
    is_own_customer: bool
) -> Decimal:
    """
    Calculate commission for a single order item.
    
    Args:
        product: Product object
        order_item: OrderItem object
        commission_rule: CommissionRule object (contains commission_type)
        is_own_customer: Whether this is the SDR's own customer
    
    Returns:
        Commission amount as Decimal
    """
    rate = commission_rule.own_customer_amount if is_own_customer else commission_rule.general_customer_amount
    
    # Use commission_type from rule, not product pricing_type
    if commission_rule.commission_type == 'per_weight':
        # Weight-based commission: rate per lb
        # Use final_weight if available, otherwise return 0 (weight not set yet)
        if order_item.final_weight:
            return Decimal(str(rate)) * order_item.final_weight
        return Decimal('0')
    else:
        # Item-based commission: rate per item (default)
        return Decimal(str(rate)) * order_item.quantity


def build_order_grouping_for_sdr(sdr: SDR, orders: List[Order]) -> Dict:
    """
    Group orders for an SDR into four categories:
    - Own customer orders
    - Other customer orders
    - No commission orders (excluded users)
    - Ineligible orders (cancelled, unpaid, or not completed)
    
    Args:
        sdr: SDR object
        orders: List of Order objects
    
    Returns:
        Dict with grouped orders and product summaries
    """
    own_customer_orders = []
    other_customer_orders = []
    no_commission_orders = []
    ineligible_orders = []

    # Get all products for product name lookup
    products_cache = {}
    excluded_user_ids = get_commission_excluded_user_ids()

    for order in orders:
        user = User.query.get(order.user_id)
        if not user:
            continue

        order_summary = _build_order_summary(order, products_cache)

        if not is_order_eligible_for_commission(order):
            ineligible_orders.append(order_summary)
            continue

        # Categorize eligible order
        if is_user_excluded_from_commission(user.id, excluded_user_ids):
            no_commission_orders.append(order_summary)
        elif user.user_source == sdr.source_identifier:
            own_customer_orders.append(order_summary)
        else:
            other_customer_orders.append(order_summary)

    return {
        'own_customer_orders': own_customer_orders,
        'other_customer_orders': other_customer_orders,
        'no_commission_orders': no_commission_orders,
        'ineligible_orders': ineligible_orders,
    }


def get_commission_summary_for_group_deal(group_deal_id: int) -> Optional[Dict]:
    """
    Get commission summary for a group deal with order grouping.
    
    Args:
        group_deal_id: ID of the group deal
    
    Returns:
        Dict with commission summary or None if not found
    """
    records = CommissionRecord.query.filter_by(group_deal_id=group_deal_id).all()
    
    if not records:
        return None
    
    orders = Order.query.filter(
        Order.group_deal_id == group_deal_id,
        Order.deleted_at.is_(None),
        Order.status == OrderStatus.COMPLETED.value,
        Order.payment_status == PaymentStatus.PAID.value,
    ).all()
    
    # Build enhanced records with order grouping
    enhanced_records = []
    for record in records:
        record_dict = record.to_dict(include_relations=True)
        
        # Get SDR for this record
        sdr = SDR.query.get(record.sdr_id)
        if sdr:
            # Build order grouping for this SDR
            order_grouping = build_order_grouping_for_sdr(sdr, orders)
            record_dict['order_grouping'] = order_grouping
        
        enhanced_records.append(record_dict)
    
    return {
        'group_deal_id': group_deal_id,
        'records': enhanced_records,
        'total_commission': sum(float(record.total_commission) for record in records)
    }
