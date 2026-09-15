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
from utils.stock_management import check_and_reserve_stock, restore_stock
from utils.sales_stats import update_product_sales_stats
from utils.order_item_delta import apply_customer_item_delta
from utils.order_item_pricing import (
    enrich_order_items,
    priced_items_from_request,
    create_order_item_rows,
)
from utils.query_batch import order_storefront_eager_options
from utils.order_audit import (
    EVENT_CUSTOMER_ITEMS_REPLACE,
    active_items_for_order,
    item_snapshot,
    record_order_audit,
)
from utils.order_totals import recalculate_order_totals, clamp_store_credit
from services import credit_service
from services import referral_service
from utils.order_payment import payment_method_error, copy_user_card_to_order
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


def _serialize_customer_order(order):
    order_dict = order.to_dict()
    group_deal = order.group_deal
    if group_deal and group_deal.deleted_at is None:
        order_dict['group_deal'] = {
            'id': group_deal.id,
            'title': group_deal.title,
            'description': group_deal.description,
            'pickup_date': group_deal.pickup_date.isoformat() if group_deal.pickup_date else None,
            'order_start_date': group_deal.order_start_date.isoformat() if group_deal.order_start_date else None,
            'order_end_date': group_deal.order_end_date.isoformat() if group_deal.order_end_date else None,
            'status': group_deal.status
        }
        order_dict.update(_customer_edit_flags(order, group_deal))
    else:
        order_dict.update(_customer_edit_flags(order, None))
    order_dict['items'] = enrich_order_items(order.items)
    if order.address:
        order_dict['address'] = order.address.to_dict()
    return order_dict


def _customer_edit_flags(order, group_deal):
    can_settings = OrderStatus.can_user_edit_settings(order.status)
    can_products = OrderStatus.can_user_edit_products(order.status, group_deal)
    return {
        'can_edit_settings': can_settings,
        'can_edit_products': can_products,
        'is_editable': can_settings,
    }


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
        orders = query.options(*order_storefront_eager_options()).order_by(Order.created_at.desc()).all()

        now = utc_now()
        auto_confirmed = False
        for order in orders:
            group_deal = order.group_deal
            if (
                group_deal
                and group_deal.deleted_at is None
                and order.status == OrderStatus.SUBMITTED.value
                and group_deal.order_end_date
                and group_deal.order_end_date < now
            ):
                order.status = OrderStatus.CONFIRMED.value
                auto_confirmed = True
                current_app.logger.info(f'Auto-confirmed order {order.id} after order_end_date')
        if auto_confirmed:
            db.session.commit()

        orders_data = [_serialize_customer_order(order) for order in orders]
        
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
        order = Order.query.options(*order_storefront_eager_options()).filter(
            Order.id == order_id
        ).filter(Order.deleted_at.is_(None)).first()
        
        if not order:
            return jsonify({
                'error': 'Order not found'
            }), 404
        
        # Check if user can access this order
        if not can_access_order(user_id, order):
            return jsonify({'error': 'Access denied'}), 403
        
        group_deal = order.group_deal
        if (
            group_deal
            and group_deal.deleted_at is None
            and order.status == OrderStatus.SUBMITTED.value
            and group_deal.order_end_date
            and group_deal.order_end_date < utc_now()
        ):
            order.status = OrderStatus.CONFIRMED.value
            db.session.commit()
            current_app.logger.info(f'Auto-confirmed order {order.id} after order_end_date')

        return jsonify({
            'order': _serialize_customer_order(order)
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
    """Create a new order. Same user may have multiple orders on one deal."""
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
        
        try:
            order_items, subtotal = priced_items_from_request(
                items, group_deal_id=group_deal_id, buyer_user_id=user_id
            )
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        user_row = User.query.filter_by(id=user_id).with_for_update().first()
        if not user_row:
            return jsonify({'error': 'User not found'}), 404

        pay_err = payment_method_error(
            delivery_method,
            payment_method,
            user_row,
            online_payment_enabled=bool(group_deal.online_payment_enabled),
            delivery_consented=bool(validated_data.get('delivery_consent')),
        )
        if pay_err:
            db.session.rollback()
            return jsonify({'error': pay_err}), 400

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
            stripe_charge_status='setup_complete' if payment_method == PaymentMethod.CARD.value else None,
            pickup_status='pending',
            status='submitted',
            notes=notes,
            store_credit_applied=Decimal('0'),
        )

        db.session.add(order)
        db.session.flush()
        if payment_method == PaymentMethod.CARD.value:
            copy_user_card_to_order(order, user_row)

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
        order_dict['items'] = enrich_order_items(order.items)
        
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
        from services import influencer_service
        influencer_service.reverse_for_order(order, reason='订单已取消')
        
        db.session.commit()
        
        current_app.logger.info(f'Order {order_id} cancelled by user {user_id}')
        
        return jsonify({
            'order': _serialize_customer_order(order),
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
        
        return jsonify({
            'order': _serialize_customer_order(order),
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
    """Customer update: settings-only omits items; item payload is an in-place delta."""
    user_id, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        order = Order.query.filter(Order.id == order_id).filter(Order.deleted_at.is_(None)).first()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if not can_access_order(user_id, order):
            return jsonify({'error': 'Access denied'}), 403
        
        group_deal = GroupDeal.query.filter(
            GroupDeal.id == order.group_deal_id,
            GroupDeal.deleted_at.is_(None)
        ).first()
        if not group_deal:
            return jsonify({'error': 'Group deal not found'}), 404
        
        validated_data, error_response, status_code = validate_request(UpdateOrderSchema)
        if error_response:
            return error_response, status_code
        
        items = validated_data.get('items') or None
        if items is not None and len(items) == 0:
            items = None
        wants_item_edit = items is not None

        if wants_item_edit:
            if not OrderStatus.can_user_edit_products(order.status, group_deal):
                if order.status != OrderStatus.SUBMITTED.value:
                    return jsonify({'error': '订单已确认，不可修改商品'}), 400
                return jsonify({'error': '团购已截单，无法修改商品'}), 400
        elif not OrderStatus.can_user_edit_settings(order.status):
            if order.status == OrderStatus.CANCELLED.value:
                return jsonify({'error': '订单已取消，无法修改'}), 400
            if order.status == OrderStatus.COMPLETED.value:
                return jsonify({'error': '订单已完成，无法修改'}), 400
            return jsonify({'error': '订单无法修改'}), 400

        delivery_method = validated_data.get('delivery_method') or order.delivery_method or DeliveryMethod.PICKUP.value
        address_id = validated_data.get('address_id')
        if 'address_id' not in validated_data:
            address_id = order.address_id
        pickup_location = validated_data.get('pickup_location')
        payment_method = validated_data.get('payment_method')
        notes = validated_data.get('notes')
        
        referral_raw = validated_data.get('referral_code')
        store_credit_raw = validated_data.get('store_credit_to_apply')
        if store_credit_raw is None:
            store_credit_raw = order.store_credit_applied
        
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

        if delivery_method == DeliveryMethod.DELIVERY.value:
            address = Address.query.filter_by(id=address_id, user_id=user_id).first()
            if not address:
                return jsonify({'error': 'Address not found or does not belong to user'}), 404
        already_delivery = order.delivery_method == DeliveryMethod.DELIVERY.value
        pay_err = payment_method_error(
            delivery_method,
            payment_method or order.payment_method,
            user_row,
            online_payment_enabled=bool(group_deal.online_payment_enabled),
            delivery_consented=bool(validated_data.get('delivery_consent')) or already_delivery,
        )
        if pay_err:
            db.session.rollback()
            return jsonify({'error': pay_err}), 400

        items_changed = False
        if wants_item_edit:
            items_before = [
                item_snapshot(i, order.order_number) for i in active_items_for_order(order.id)
            ]
            items_changed, item_err = apply_customer_item_delta(
                order, items, buyer_user_id=user_id
            )
            if item_err:
                db.session.rollback()
                return jsonify({'error': item_err}), 400
            if items_changed:
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

        order.delivery_method = delivery_method
        order.address_id = address_id
        if 'pickup_location' in validated_data:
            order.pickup_location = pickup_location if delivery_method == DeliveryMethod.PICKUP.value else None
        if 'notes' in validated_data:
            order.notes = notes
        if payment_method and payment_method in PaymentMethod.get_all_values():
            order.payment_method = payment_method
        if order.payment_method == PaymentMethod.CARD.value:
            copy_user_card_to_order(order, user_row)
        order.updated_at = utc_now()

        try:
            _apply_store_credit_and_recalc(order, user_row, store_credit_raw)
        except ValueError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
        
        db.session.commit()
        db.session.refresh(order)
        
        if items_changed:
            try:
                update_product_sales_stats(order)
            except Exception as e:
                current_app.logger.warning(f'Failed to update sales stats: {e}')
        
        return jsonify({
            'order': _serialize_customer_order(order),
            'message': 'Order updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating order: {e}', exc_info=True)
        return jsonify({
            'error': 'Failed to update order',
            'message': str(e)
        }), 500

