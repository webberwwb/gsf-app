from flask import Blueprint, jsonify, request, current_app
from models import db
from models.order import Order, OrderItem
from models.groupdeal import GroupDeal
from models.product import Product
from models.user import User, AuthToken
from models.address import Address
from datetime import datetime, timezone
from models.base import utc_now
from constants.status_enums import OrderStatus, PaymentStatus, DeliveryMethod, PaymentMethod, GroupDealStatus
from schemas.order import CreateOrderSchema, UpdateOrderSchema
from schemas.utils import validate_request
from decimal import Decimal
from utils.stock_management import check_and_reserve_stock, restore_stock, update_stock_after_order_modification
from utils.sales_stats import update_product_sales_stats
from utils.order_item_pricing import (
    enrich_order_item_dict,
    priced_items_from_request,
    create_order_item_rows,
)
from utils.order_audit import (
    EVENT_CUSTOMER_ITEMS_REPLACE,
    active_items_for_order,
    apply_item_sources_from_request,
    item_snapshot,
    record_order_audit,
)
from utils.order_totals import recalculate_order_totals, clamp_store_credit
from services import credit_service
from services import referral_service
import random
import string

orders_bp = Blueprint('orders', __name__)


def _apply_store_credit_and_recalc(order, user_row, store_credit_raw):
    """Recalculate totals, apply credit, recalc shipping tier with credit/adjustment."""
    recalculate_order_totals(order)
    req_dec = Decimal(str(store_credit_raw)) if store_credit_raw is not None else Decimal('0')
    if req_dec < 0:
        req_dec = Decimal('0')
    max_a = credit_service.compute_max_credit_apply(user_row, order.total)
    applied = min(req_dec, max_a)
    credit_service.apply_order_store_credit_spend(user_row, order, applied)
    recalculate_order_totals(order)
    clamp_store_credit(order)
    recalculate_order_totals(order)


def require_auth():
    """Check if user is authenticated and return user_id"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '').strip()
    else:
        token = auth_header.strip()
    
    if not token:
        return None, jsonify({'error': 'No token provided'}), 401
    
    auth_token = AuthToken.query.filter_by(token=token, is_revoked=False).first()
    if not auth_token or not auth_token.is_valid():
        return None, jsonify({'error': 'Invalid or expired token'}), 401
    
    # Get user
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None, jsonify({'error': 'User not found or inactive'}), 401
    
    return user.id, None, None

def can_access_order(user_id, order):
    """Check if user can access an order (user owns it or is admin)"""
    if not order:
        return False
    
    # User owns the order
    if order.user_id == user_id:
        return True
    
    # Check if user is admin
    user = User.query.get(user_id)
    if user and user.is_admin:
        return True
    
    return False


@orders_bp.route('/orders', methods=['GET'])
def get_user_orders():
    """Get all orders for the current authenticated user"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get query parameters
        status_filter = request.args.get('status', '').strip()  # 'pending', 'confirmed', 'completed', 'cancelled'
        payment_status_filter = request.args.get('payment_status', '').strip()  # 'pending', 'paid', 'failed', 'refunded'
        group_deal_id = request.args.get('group_deal_id')  # Filter by group deal
        
        # Build query - filter out soft-deleted orders
        query = Order.query.filter_by(user_id=user_id).filter(Order.deleted_at.is_(None))
        
        # Apply filters
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        if payment_status_filter:
            query = query.filter(Order.payment_status == payment_status_filter)
        
        if group_deal_id:
            query = query.filter(Order.group_deal_id == int(group_deal_id))
        
        # Order by creation date (newest first)
        query = query.order_by(Order.created_at.desc())
        
        orders = query.all()
        
        # Build response with order details
        orders_data = []
        for order in orders:
            order_dict = order.to_dict()
            
            # Get group deal info (excluding soft-deleted)
            group_deal = GroupDeal.query.filter(
                GroupDeal.id == order.group_deal_id,
                GroupDeal.deleted_at.is_(None)
            ).first()
            if group_deal:
                # Auto-confirm order if past order_end_date but still submitted
                now = utc_now()
                if order.status == OrderStatus.SUBMITTED.value and group_deal.order_end_date < now:
                    order.status = OrderStatus.CONFIRMED.value
                    db.session.commit()
                    current_app.logger.info(f'Auto-confirmed order {order.id} after order_end_date')
                
                order_dict['group_deal'] = {
                    'id': group_deal.id,
                    'title': group_deal.title,
                    'description': group_deal.description,
                    'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
                    'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
                    'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None,
                    'status': group_deal.status
                }
                # User can only edit/cancel when order status is 'submitted'
                order_dict['is_editable'] = order.status == OrderStatus.SUBMITTED.value
            
            order_dict['items'] = [
                enrich_order_item_dict(item) for item in order.items
            ]
            
            # Get address info if delivery order
            if order.address_id:
                address = Address.query.get(order.address_id)
                if address:
                    order_dict['address'] = address.to_dict()
            
            orders_data.append(order_dict)
        
        return jsonify({
            'orders': orders_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching user orders: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch orders',
            'message': str(e)
        }), 500

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a single order by ID (must belong to current user or user must be admin)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id).filter(Order.deleted_at.is_(None)).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found'
            }), 404
        
        # Check if user can access this order
        if not can_access_order(user_id, order):
            return jsonify({'error': 'Access denied'}), 403
        
        order_dict = order.to_dict()
        
        # Get group deal info (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if group_deal:
            # Auto-confirm order if past order_end_date but still submitted
            now = utc_now()
            if order.status == OrderStatus.SUBMITTED.value and group_deal.order_end_date < now:
                order.status = OrderStatus.CONFIRMED.value
                db.session.commit()
                current_app.logger.info(f'Auto-confirmed order {order.id} after order_end_date')
            
            order_dict['group_deal'] = {
                'id': group_deal.id,
                'title': group_deal.title,
                'description': group_deal.description,
                'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
                'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
                'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None,
                'status': group_deal.status
            }
            # User can only edit/cancel when order status is 'submitted'
            order_dict['is_editable'] = order.status == OrderStatus.SUBMITTED.value
        
        # Get order items with product details
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
        return jsonify({
            'order': order_dict
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'Error fetching order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to fetch order',
            'message': str(e)
        }), 500

def generate_order_number():
    """Generate a unique order number"""
    timestamp = utc_now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'GSF-{timestamp}-{random_suffix}'

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    """Create a new order or update existing order for the same group deal"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Validate request data using schema
        validated_data, error_response, status_code = validate_request(CreateOrderSchema)
        if error_response:
            return error_response, status_code
        
        group_deal_id = validated_data['group_deal_id']
        items = validated_data['items']
        delivery_method = validated_data['delivery_method']
        address_id = validated_data.get('address_id')
        pickup_location = validated_data.get('pickup_location')
        payment_method = validated_data['payment_method']
        notes = validated_data.get('notes')  # User custom notes
        
        referral_raw = validated_data.get('referral_code')
        store_credit_raw = validated_data.get('store_credit_to_apply')
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        # Check if group deal is still accepting orders
        now = utc_now()
        if group_deal.order_end_date and group_deal.order_end_date < now:
            return jsonify({'error': 'This group deal is no longer accepting orders'}), 400
        
        # Allow multiple orders per group deal - users can place multiple orders
        
        # Check and reserve stock (with row-level locking for concurrency safety)
        stock_available, error_msg = check_and_reserve_stock(group_deal_id, items)
        if not stock_available:
            return jsonify({'error': error_msg}), 400
        
        # Verify address belongs to user if delivery method is selected
        if delivery_method == DeliveryMethod.DELIVERY.value:
            address = Address.query.filter_by(id=address_id, user_id=user_id).first()
            if not address:
                return jsonify({'error': 'Address not found or does not belong to user'}), 404
            # Delivery orders must use etransfer payment method
            if payment_method == PaymentMethod.CASH.value:
                return jsonify({'error': '配送订单必须使用电子转账支付'}), 400
        
        try:
            order_items, subtotal = priced_items_from_request(items)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        user_row = User.query.filter_by(id=user_id).with_for_update().first()
        if not user_row:
            return jsonify({'error': 'User not found'}), 404

        if referral_raw and not user_row.referred_by_user_id:
            ok, err = referral_service.try_bind_referral(user_row, referral_raw)
            if not ok:
                db.session.rollback()
                return jsonify({'error': err}), 400
            db.session.refresh(user_row)

        order_number = generate_order_number()

        if payment_method not in PaymentMethod.get_all_values():
            payment_method = PaymentMethod.CASH.value

        order = Order(
            user_id=user_id,
            group_deal_id=group_deal_id,
            address_id=address_id,
            delivery_method=delivery_method,
            pickup_location=pickup_location if delivery_method == DeliveryMethod.PICKUP.value else None,
            order_number=order_number,
            subtotal=Decimal('0'),
            tax=Decimal('0'),
            shipping_fee=Decimal('0'),
            total=Decimal('0'),
            points_earned=0,
            payment_method=payment_method,
            payment_status='unpaid',
            pickup_status='pending',
            status='submitted',
            notes=notes,
            store_credit_applied=Decimal('0'),
        )

        db.session.add(order)
        db.session.flush()

        create_order_item_rows(order.id, order_items, db.session)

        try:
            _apply_store_credit_and_recalc(order, user_row, store_credit_raw)
        except ValueError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
        
        # Commit transaction
        db.session.commit()
        
        # Update product sales stats
        try:
            update_product_sales_stats(order)
        except Exception as e:
            current_app.logger.warning(f'Failed to update sales stats: {e}')
        
        # Return created order
        order_dict = order.to_dict()
        
        # Get group deal info
        order_dict['group_deal'] = {
            'id': group_deal.id,
            'title': group_deal.title,
            'description': group_deal.description,
            'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None
        }
        
        # Get order items with product details
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
        return jsonify({
            'order': order_dict,
            'message': 'Order created successfully',
            'is_new': True
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to create order',
            'message': str(e)
        }), 500

@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order (only if still within order window)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get the order
        order = Order.query.filter(Order.id == order_id).filter(Order.deleted_at.is_(None)).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check if user can access this order
        if not can_access_order(user_id, order):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if order is already cancelled
        if order.status == OrderStatus.CANCELLED.value:
            return jsonify({'error': '订单已取消'}), 400
        
        # User can only cancel if order status is 'submitted'
        if order.status != 'submitted':
            return jsonify({'error': '订单已确认，无法取消'}), 400
        
        # Get group deal for response (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        # Restore stock for cancelled order
        items_to_restore = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
        try:
            restore_stock(order.group_deal_id, items_to_restore)
        except Exception as e:
            current_app.logger.error(f'Failed to restore stock on cancellation: {e}')
            # Continue with cancellation even if stock restoration fails
        
        # Cancel the order
        user_row = User.query.get(order.user_id)
        if user_row:
            credit_service.refund_order_store_credit(order, user_row)
        order.status = OrderStatus.CANCELLED.value
        order.updated_at = utc_now()
        
        db.session.commit()
        
        current_app.logger.info(f'Order {order_id} cancelled by user {user_id}')
        
        # Return updated order
        order_dict = order.to_dict()
        
        # Get group deal info
        order_dict['group_deal'] = {
            'id': group_deal.id,
            'title': group_deal.title,
            'description': group_deal.description,
            'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
            'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
            'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None
        }
        order_dict['is_editable'] = False  # Cancelled orders are not editable
        
        # Get order items with product details
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
        return jsonify({
            'order': order_dict,
            'message': 'Order cancelled successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error cancelling order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to cancel order',
            'message': str(e)
        }), 500

@orders_bp.route('/orders/<int:order_id>/reactivate', methods=['POST'])
def reactivate_order(order_id):
    """Reactivate a cancelled order (change status back to submitted)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get the order
        order = Order.query.filter(Order.id == order_id).filter(Order.deleted_at.is_(None)).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check if user can access this order
        if not can_access_order(user_id, order):
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if order is cancelled
        if order.status != OrderStatus.CANCELLED.value:
            return jsonify({'error': '只能重新激活已取消的订单'}), 400
        
        # Get group deal for validation (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        # Check if group deal is still accepting orders
        now = utc_now()
        if group_deal.order_end_date and group_deal.order_end_date < now:
            return jsonify({'error': '团购已截单，无法提交订单'}), 400
        
        if group_deal.status == GroupDealStatus.CLOSED.value:
            return jsonify({'error': '团购已截单，无法提交订单'}), 400
        
        # Check and reserve stock again (with row-level locking for concurrency safety)
        items_to_reserve = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
        stock_available, error_msg = check_and_reserve_stock(order.group_deal_id, items_to_reserve)
        if not stock_available:
            return jsonify({'error': error_msg}), 400
        
        # Reactivate the order
        order.status = OrderStatus.SUBMITTED.value
        order.updated_at = utc_now()
        
        db.session.commit()
        
        current_app.logger.info(f'Order {order_id} reactivated by user {user_id}')
        
        # Return updated order
        order_dict = order.to_dict()
        
        # Get group deal info
        order_dict['group_deal'] = {
            'id': group_deal.id,
            'title': group_deal.title,
            'description': group_deal.description,
            'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
            'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
            'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None,
            'status': group_deal.status
        }
        order_dict['is_editable'] = True  # Reactivated orders are editable
        
        # Get order items with product details
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
        return jsonify({
            'order': order_dict,
            'message': '订单已重新激活'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error reactivating order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to reactivate order',
            'message': str(e)
        }), 500

@orders_bp.route('/orders/<int:order_id>', methods=['PATCH'])
def update_order(order_id):
    """Update an existing order (only if still within order window)"""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        # Get the order
        order = Order.query.filter(Order.id == order_id).filter(Order.deleted_at.is_(None)).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check if user can access this order
        if not can_access_order(user_id, order):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get group deal for validation (excluding soft-deleted)
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        # Validate request data using schema
        validated_data, error_response, status_code = validate_request(UpdateOrderSchema)
        if error_response:
            return error_response, status_code
        
        items = validated_data['items']
        delivery_method = validated_data['delivery_method']
        address_id = validated_data.get('address_id')
        pickup_location = validated_data.get('pickup_location')
        payment_method = validated_data.get('payment_method')
        notes = validated_data.get('notes')  # User custom notes
        
        referral_raw = validated_data.get('referral_code')
        store_credit_raw = validated_data.get('store_credit_to_apply')
        
        user_row = User.query.filter_by(id=user_id).with_for_update().first()
        if not user_row:
            return jsonify({'error': 'User not found'}), 404
        credit_service.refund_order_store_credit(order, user_row)
        if referral_raw and not user_row.referred_by_user_id:
            ok, err = referral_service.try_bind_referral(user_row, referral_raw)
            if not ok:
                db.session.rollback()
                return jsonify({'error': err}), 400
        db.session.refresh(user_row)
        
        # Check if items are being changed by comparing with existing order items
        existing_items = {(item.product_id, item.quantity) for item in order.items}
        new_items = {(item_data['product_id'], item_data['quantity']) for item_data in items}
        items_changed = existing_items != new_items
        
        # If items are being changed, we need to update stock
        if items_changed:
            # Prepare items lists for stock management
            old_items_list = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items]
            new_items_list = [{'product_id': item_data['product_id'], 'quantity': item_data['quantity']} for item_data in items]
            
            # Check and update stock (with row-level locking for concurrency safety)
            stock_available, error_msg = update_stock_after_order_modification(
                order.group_deal_id, old_items_list, new_items_list
            )
            if not stock_available:
                return jsonify({'error': error_msg}), 400
        
        # Check if delivery method is being changed
        current_delivery_method = order.delivery_method or DeliveryMethod.PICKUP.value
        delivery_method_changed = delivery_method != current_delivery_method
        
        # If items are being changed, enforce normal restrictions
        if items_changed:
            # User can only edit items if order status is 'submitted'
            # Confirmed orders (including when group deal is closed) cannot edit products
            if order.status != 'submitted':
                return jsonify({'error': '订单已确认，不可修改商品'}), 400
            
            # Check if still within order window
            now = utc_now()
            if group_deal.order_end_date and group_deal.order_end_date < now:
                return jsonify({'error': '团购已截单，无法修改商品'}), 400
        
        # If only delivery method or payment method is being changed, allow it even after deadline
        # But still check order status - can't change if order is cancelled or completed
        # Confirmed orders (including when group deal is closed) can still edit pickup/payment method
        if (delivery_method_changed or payment_method) and not items_changed:
            if order.status == 'cancelled':
                return jsonify({'error': '订单已取消，无法修改'}), 400
            if order.status == 'completed':
                return jsonify({'error': '订单已完成，无法修改'}), 400
            # Allow delivery/payment method update even after order_end_date or for confirmed orders
        
        # Verify address belongs to user if delivery method is selected
        if delivery_method == DeliveryMethod.DELIVERY.value:
            address = Address.query.filter_by(id=address_id, user_id=user_id).first()
            if not address:
                return jsonify({'error': 'Address not found or does not belong to user'}), 404
            # Delivery orders must use etransfer payment method
            if payment_method == PaymentMethod.CASH.value:
                return jsonify({'error': '配送订单必须使用电子转账支付'}), 400
        
        unavailable_by_item_id = {item.id: item.is_unavailable for item in order.items}
        try:
            new_order_items, subtotal = priced_items_from_request(items, unavailable_by_item_id)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        items_before = [
            item_snapshot(i, order.order_number) for i in active_items_for_order(order.id)
        ]
        apply_item_sources_from_request(new_order_items, order.id, items)

        OrderItem.soft_delete_for_order(order.id, db.session)

        order.delivery_method = delivery_method
        order.address_id = address_id
        if 'pickup_location' in validated_data:
            order.pickup_location = pickup_location if delivery_method == DeliveryMethod.PICKUP.value else None
        if 'notes' in validated_data:
            order.notes = notes
        if payment_method and payment_method in PaymentMethod.get_all_values():
            order.payment_method = payment_method
        order.updated_at = utc_now()

        create_order_item_rows(order.id, new_order_items, db.session)
        db.session.flush()

        items_after = [
            item_snapshot(i, order.order_number) for i in active_items_for_order(order.id)
        ]
        record_order_audit(
            order.id,
            EVENT_CUSTOMER_ITEMS_REPLACE,
            {
                'order_number': order.order_number,
                'items_before': items_before,
                'items_after': items_after,
            },
            actor_user_id=user_id,
        )

        try:
            _apply_store_credit_and_recalc(order, user_row, store_credit_raw)
        except ValueError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
        
        # Commit transaction
        db.session.commit()
        
        # Refresh the order from database to ensure we have latest data
        db.session.refresh(order)
        
        # Update product sales stats
        try:
            update_product_sales_stats(order)
        except Exception as e:
            current_app.logger.warning(f'Failed to update sales stats: {e}')
        
        # Return updated order
        order_dict = order.to_dict()
        
        # Get group deal info
        order_dict['group_deal'] = {
            'id': group_deal.id,
            'title': group_deal.title,
            'description': group_deal.description,
            'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
            'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
            'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None,
            'status': group_deal.status
        }
        # User can only edit/cancel when order status is 'submitted'
        order_dict['is_editable'] = order.status == OrderStatus.SUBMITTED.value
        
        # Get order items with product details
        order_dict['items'] = [enrich_order_item_dict(item) for item in order.items]
        
        return jsonify({
            'order': order_dict,
            'message': 'Order updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order',
            'message': str(e)
        }), 500

