"""
Commission calculation utilities for SDR commission management.
"""
from decimal import Decimal
from typing import Dict, List, Optional
from models import db
from models.sdr import SDR, CommissionRule, CommissionRecord
from models.groupdeal import GroupDeal
from models.order import Order, OrderItem
from models.product import Product
from models.user import User


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
    
    # Get all orders for this group deal (exclude soft-deleted orders)
    orders = Order.query.filter_by(
        group_deal_id=group_deal_id,
        deleted_at=None
    ).all()
    
    if not orders:
        return {'success': True, 'records': [], 'total_commission': 0, 'message': 'No orders found'}
    
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
    
    # Process each order
    for order in orders:
        # Get user to check source
        user = User.query.get(order.user_id)
        if not user:
            continue
        
        # Hardcoded rule: Skip commission calculation for 谷语农庄 (phone: +14373406925)
        if user.phone == '+14373406925':
            continue
        
        is_own_customer = (user.user_source == sdr.source_identifier)
        
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
    Group orders for an SDR into three categories:
    - Own customer orders
    - Other customer orders
    - No commission orders (谷语农庄)
    
    Args:
        sdr: SDR object
        orders: List of Order objects
    
    Returns:
        Dict with grouped orders and product summaries
    """
    own_customer_orders = []
    other_customer_orders = []
    no_commission_orders = []
    
    # Get all products for product name lookup
    products_cache = {}
    
    for order in orders:
        user = User.query.get(order.user_id)
        if not user:
            continue
        
        # Build order summary with product details
        order_items_summary = []
        for item in order.items:
            if item.product_id not in products_cache:
                product = Product.query.get(item.product_id)
                if product:
                    products_cache[item.product_id] = product.name
                else:
                    products_cache[item.product_id] = f"Product {item.product_id}"
            
            product_name = products_cache[item.product_id]
            
            item_summary = {
                'product_id': item.product_id,
                'product_name': product_name,
                'quantity': item.quantity,
                'weight': float(item.final_weight) if item.final_weight else None,
                'unit_price': float(item.unit_price) if item.unit_price else None,
                'subtotal': float(item.total_price) if item.total_price else None
            }
            order_items_summary.append(item_summary)
        
        # Get user display name (prefer nickname, fallback to wechat_nickname or phone)
        user_name = None
        if user:
            user_name = user.nickname or user.wechat_nickname or user.phone or f"User {user.id}"
        
        order_summary = {
            'order_id': order.id,
            'order_number': order.order_number,
            'user_id': order.user_id,
            'user_name': user_name,
            'user_phone': user.phone if user else None,
            'user_source': user.user_source if user else None,
            'items': order_items_summary,
            'total': float(order.total) if order.total else 0.0
        }
        
        # Categorize order
        if user.phone == '+14373406925':
            # No commission orders (谷语农庄)
            no_commission_orders.append(order_summary)
        elif user.user_source == sdr.source_identifier:
            # Own customer orders
            own_customer_orders.append(order_summary)
        else:
            # Other customer orders
            other_customer_orders.append(order_summary)
    
    return {
        'own_customer_orders': own_customer_orders,
        'other_customer_orders': other_customer_orders,
        'no_commission_orders': no_commission_orders
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
    
    # Get all orders for this group deal
    orders = Order.query.filter_by(
        group_deal_id=group_deal_id,
        deleted_at=None
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
