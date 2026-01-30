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
from utils.shipping import calculate_shipping_fee
from utils.sales_stats import update_product_sales_stats
import random
import string

orders_bp = Blueprint('orders', __name__)

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
            
            # Get order items with product details
            items_data = []
            for item in order.items:
                item_dict = item.to_dict()
                product = Product.query.get(item.product_id)
                if product:
                    item_dict['product'] = {
                        'id': product.id,
                        'name': product.name,
                        'image': product.image,
                        'pricing_type': product.pricing_type,
                        'pricing_data': product.pricing_data
                    }
                items_data.append(item_dict)
            
            order_dict['items'] = items_data
            
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
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type,
                    'description': product.description,
                    'pricing_data': product.pricing_data
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
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
        
        # Validate group deal exists and is active (excluding soft-deleted)
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
        
        # Calculate order totals
        subtotal = Decimal('0')
        order_items = []
        
        for item_data in items:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            pricing_type = item_data.get('pricing_type', 'per_item')
            
            # Get product
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            # ============================================================================
            # CRITICAL: Calculate item price based on pricing type
            # ============================================================================
            # This logic MUST handle ALL pricing types correctly, especially when
            # final_weight is provided. DO NOT REMOVE OR SIMPLIFY WITHOUT TESTING!
            #
            # Pricing types:
            # 1. per_item: Fixed price per item
            # 2. weight_range: Price based on weight ranges (use lowest for estimation)
            # 3. unit_weight: Price = weight × price_per_unit
            # 4. bundled_weight: Price = final_weight × price_per_unit (e.g., 3.77 lb × $6.99/lb)
            #
            # REGRESSION WARNING: bundled_weight MUST calculate using final_weight when provided!
            # Bug example: User enters final_weight = 3.77 lb for $6.99/lb product
            # - Expected: $26.35 (3.77 × 6.99)
            # - Bug: $38.45 (using estimated mid-weight instead of actual weight)
            # ============================================================================
            
            # Calculate item price based on pricing type
            if pricing_type == 'per_item':
                # Use product's default price
                unit_price = product.get_display_price() or 0
                total_price = unit_price * quantity
            elif pricing_type == 'weight_range':
                # For estimation without final_weight, use first range (lowest weight)
                ranges = product.pricing_data.get('ranges', []) if product.pricing_data else []
                if ranges:
                    unit_price = float(ranges[0].get('price', 0))
                else:
                    unit_price = 0
                total_price = unit_price * quantity
            elif pricing_type == 'unit_weight':
                # unit_weight: price_per_unit is price per unit weight
                # unit_price = price_per_unit (the rate)
                # total_price = price_per_unit * final_weight (or estimated weight)
                # Quantity is always 1 for weight-based products (they're weighed individually, not stacked)
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                final_weight = item_data.get('final_weight')
                
                unit_price = price_per_unit  # Unit price is the rate itself
                
                if final_weight is not None:
                    try:
                        final_weight_float = float(final_weight)
                        if final_weight_float > 0 and price_per_unit > 0:
                            total_price = price_per_unit * final_weight_float
                        else:
                            # Invalid weight, use estimated weight
                            estimated_weight = 1  # Minimum 1 unit for estimation
                            total_price = price_per_unit * estimated_weight
                    except (ValueError, TypeError):
                        # Invalid weight, use estimated weight
                        estimated_weight = 1  # Minimum 1 unit for estimation
                        total_price = price_per_unit * estimated_weight
                else:
                    # No final_weight, use estimated weight
                    estimated_weight = 1  # Minimum 1 unit for estimation
                    total_price = price_per_unit * estimated_weight
            elif pricing_type == 'bundled_weight':
                # Bundled weight: products are weighed individually, not stacked
                # unit_price = price_per_unit (the rate)
                # total_price = price_per_unit * final_weight (or estimated weight)
                # Quantity is always 1 for weight-based products (they're weighed individually, not stacked)
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                final_weight = item_data.get('final_weight')
                
                unit_price = price_per_unit  # Unit price is the rate itself
                
                # Convert final_weight to float if provided and valid
                if final_weight is not None:
                    try:
                        final_weight_float = float(final_weight)
                        if final_weight_float > 0 and price_per_unit > 0:
                            total_price = price_per_unit * final_weight_float
                        else:
                            final_weight = None  # Invalid weight or no price_per_unit, use estimation
                    except (ValueError, TypeError):
                        final_weight = None  # Invalid weight, use estimation
                
                # Use estimation if no valid final_weight or price_per_unit is 0
                if final_weight is None:
                    if price_per_unit > 0:
                        # Use min-weight for conservative estimation
                        min_weight = float(product.pricing_data.get('min_weight', 7) if product.pricing_data else 7)
                        total_price = price_per_unit * min_weight
                    else:
                        # price_per_unit is 0 or missing - unit_price stays as price_per_unit (0)
                        # No fallback - unit_price should always be price_per_unit from DB
                        total_price = 0
            else:
                unit_price = product.get_display_price() or 0
                total_price = unit_price * quantity
            
            subtotal += Decimal(str(total_price))
            
            order_items.append({
                'product_id': product_id,
                'product': product,  # Include product object for shipping calculation
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'final_weight': item_data.get('final_weight')  # Include weight for bundled_weight products
            })
        
        # Calculate shipping fee
        address = None
        if delivery_method == DeliveryMethod.DELIVERY.value and address_id:
            address = Address.query.get(address_id)
        
        shipping_fee = calculate_shipping_fee(subtotal, delivery_method, address, order_items)
        
        # Calculate tax (0% for now, can be configured later)
        tax = Decimal('0')
        total = subtotal + tax + shipping_fee
        
        # Calculate points (1 point per dollar, excluding shipping fee)
        points_earned = int(subtotal + tax)
        
        # Generate unique order number
        order_number = generate_order_number()
        
        # Validate payment method
        if payment_method not in PaymentMethod.get_all_values():
            payment_method = PaymentMethod.CASH.value
        
        # Create order
        order = Order(
            user_id=user_id,
            group_deal_id=group_deal_id,
            address_id=address_id,
            delivery_method=delivery_method,
            pickup_location=pickup_location if delivery_method == DeliveryMethod.PICKUP.value else None,
            order_number=order_number,
            subtotal=subtotal,
            tax=tax,
            shipping_fee=shipping_fee,
            total=total,
            points_earned=points_earned,
            payment_method=payment_method,
            payment_status='unpaid',
            pickup_status='pending',
            status='submitted',
            notes=notes  # User custom notes
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items:
            # Get final_weight, convert to float if provided, otherwise None
            final_weight = item_data.get('final_weight')
            if final_weight is not None:
                try:
                    final_weight = float(final_weight)
                    # Only save if weight is positive
                    if final_weight <= 0:
                        final_weight = None
                except (ValueError, TypeError):
                    final_weight = None
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price'],
                final_weight=final_weight  # Save weight for bundled_weight products
            )
            db.session.add(order_item)
        
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
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type,
                    'pricing_data': product.pricing_data
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
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
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type,
                    'pricing_data': product.pricing_data
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
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
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type,
                    'pricing_data': product.pricing_data
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
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
        
        # Calculate new order totals
        subtotal = Decimal('0')
        new_order_items = []
        
        for item_data in items:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            pricing_type = item_data.get('pricing_type', 'per_item')
            
            # Get product
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': f'Product {product_id} not found'}), 404
            
            # ============================================================================
            # CRITICAL: Calculate item price based on pricing type
            # ============================================================================
            # This logic MUST handle ALL pricing types correctly, especially when
            # final_weight is provided. DO NOT REMOVE OR SIMPLIFY WITHOUT TESTING!
            #
            # Pricing types:
            # 1. per_item: Fixed price per item
            # 2. weight_range: Price based on weight ranges
            # 3. unit_weight: Price = weight × price_per_unit
            # 4. bundled_weight: Price = final_weight × price_per_unit (e.g., 3.77 lb × $6.99/lb)
            #
            # REGRESSION WARNING: bundled_weight MUST calculate using final_weight when provided!
            # Bug example: User enters final_weight = 3.77 lb for $6.99/lb product
            # - Expected: $26.35 (3.77 × 6.99)
            # - Bug: $38.45 (using estimated mid-weight instead of actual weight)
            # ============================================================================
            
            # Calculate item price based on pricing type
            if pricing_type == 'per_item':
                # Use product's default price
                unit_price = product.get_display_price() or 0
                total_price = unit_price * quantity
            elif pricing_type == 'weight_range':
                final_weight = item_data.get('final_weight')
                ranges = product.pricing_data.get('ranges', []) if product.pricing_data else []
                
                if final_weight is not None and ranges:
                    try:
                        final_weight_float = float(final_weight)
                        if final_weight_float > 0:
                            # Find matching range based on final_weight
                            matched_price = None
                            for range_item in ranges:
                                min_weight = range_item.get('min', 0)
                                max_weight = range_item.get('max')
                                if final_weight_float >= min_weight and (max_weight is None or final_weight_float < max_weight):
                                    matched_price = float(range_item.get('price', 0))
                                    break
                            
                            if matched_price is not None:
                                # Use the matched range price (selected from DB based on weight)
                                unit_price = matched_price
                                total_price = unit_price * quantity
                            else:
                                # No matching range, use first range (lowest weight) for estimation
                                unit_price = float(ranges[0].get('price', 0)) if ranges else 0
                                total_price = unit_price * quantity
                        else:
                            # Invalid weight, use first range (lowest weight) for estimation
                            unit_price = float(ranges[0].get('price', 0)) if ranges else 0
                            total_price = unit_price * quantity
                    except (ValueError, TypeError):
                        # Invalid weight, use first range (lowest weight) for estimation
                        unit_price = float(ranges[0].get('price', 0)) if ranges else 0
                        total_price = unit_price * quantity
                else:
                    # No final_weight, use first range (lowest weight) for estimation
                    unit_price = float(ranges[0].get('price', 0)) if ranges else 0
                    total_price = unit_price * quantity
            elif pricing_type == 'unit_weight':
                # unit_weight: price_per_unit is price per unit weight
                # unit_price = price_per_unit (the rate)
                # total_price = price_per_unit * final_weight (or estimated weight)
                # Quantity is always 1 for weight-based products (they're weighed individually, not stacked)
                final_weight = item_data.get('final_weight')
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                
                unit_price = price_per_unit  # Unit price is the rate itself
                
                if final_weight is not None:
                    try:
                        final_weight_float = float(final_weight)
                        if final_weight_float > 0 and price_per_unit > 0:
                            total_price = price_per_unit * final_weight_float
                        else:
                            # Invalid weight, use estimated weight
                            estimated_weight = 1  # Minimum 1 unit for estimation
                            total_price = price_per_unit * estimated_weight
                    except (ValueError, TypeError):
                        # Invalid weight, use estimated weight
                        estimated_weight = 1  # Minimum 1 unit for estimation
                        total_price = price_per_unit * estimated_weight
                else:
                    # No final_weight, use estimated weight
                    estimated_weight = 1  # Minimum 1 unit for estimation
                    total_price = price_per_unit * estimated_weight
            elif pricing_type == 'bundled_weight':
                # Bundled weight: products are weighed individually, not stacked
                # unit_price = price_per_unit (the rate)
                # total_price = price_per_unit * final_weight (or estimated weight)
                # Quantity is always 1 for weight-based products (they're weighed individually, not stacked)
                price_per_unit = float(product.pricing_data.get('price_per_unit', 0) if product.pricing_data else 0)
                final_weight = item_data.get('final_weight')
                
                unit_price = price_per_unit  # Unit price is the rate itself
                
                # Convert final_weight to float if provided and valid
                if final_weight is not None:
                    try:
                        final_weight_float = float(final_weight)
                        if final_weight_float > 0 and price_per_unit > 0:
                            total_price = price_per_unit * final_weight_float
                        else:
                            final_weight = None  # Invalid weight or no price_per_unit, use estimation
                    except (ValueError, TypeError):
                        final_weight = None  # Invalid weight, use estimation
                
                # Use estimation if no valid final_weight or price_per_unit is 0
                if final_weight is None:
                    if price_per_unit > 0:
                        # Use min-weight for conservative estimation
                        min_weight = float(product.pricing_data.get('min_weight', 7) if product.pricing_data else 7)
                        total_price = price_per_unit * min_weight
                    else:
                        # price_per_unit is 0 or missing - unit_price stays as price_per_unit (0)
                        # No fallback - unit_price should always be price_per_unit from DB
                        total_price = 0
            else:
                unit_price = product.get_display_price() or 0
                total_price = unit_price * quantity
            
            subtotal += Decimal(str(total_price))
            
            new_order_items.append({
                'product_id': product_id,
                'product': product,  # Include product object for shipping calculation
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price,
                'final_weight': item_data.get('final_weight')  # Include weight for bundled_weight products
            })
        
        # Calculate shipping fee
        address = None
        if delivery_method == DeliveryMethod.DELIVERY.value and address_id:
            address = Address.query.get(address_id)
        
        shipping_fee = calculate_shipping_fee(subtotal, delivery_method, address, new_order_items)
        
        # Calculate tax (0% for now, can be configured later)
        tax = Decimal('0')
        total = subtotal + tax + shipping_fee
        
        # Calculate points (1 point per dollar, excluding shipping fee)
        points_earned = int(subtotal + tax)
        
        # Delete old order items
        OrderItem.query.filter_by(order_id=order.id).delete()
        
        # Update order totals, delivery method, address, pickup location, and payment method
        order.subtotal = subtotal
        order.tax = tax
        order.shipping_fee = shipping_fee
        order.total = total
        order.points_earned = points_earned
        order.delivery_method = delivery_method
        order.address_id = address_id
        
        # Update pickup_location (only for pickup orders)
        if 'pickup_location' in validated_data:
            order.pickup_location = pickup_location if delivery_method == DeliveryMethod.PICKUP.value else None
        
        # Update notes (user custom notes)
        if 'notes' in validated_data:
            order.notes = notes
        
        if payment_method and payment_method in PaymentMethod.get_all_values():
            order.payment_method = payment_method
        order.updated_at = utc_now()
        
        # Create new order items
        for item_data in new_order_items:
            # Get final_weight, convert to float if provided, otherwise None
            final_weight = item_data.get('final_weight')
            if final_weight is not None:
                try:
                    final_weight = float(final_weight)
                    # Only save if weight is positive
                    if final_weight <= 0:
                        final_weight = None
                except (ValueError, TypeError):
                    final_weight = None
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price'],
                final_weight=final_weight  # Save weight for bundled_weight products
            )
            db.session.add(order_item)
        
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
        items_data = []
        for item in order.items:
            item_dict = item.to_dict()
            product = Product.query.get(item.product_id)
            if product:
                item_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'image': product.image,
                    'pricing_type': product.pricing_type,
                    'pricing_data': product.pricing_data
                }
            items_data.append(item_dict)
        
        order_dict['items'] = items_data
        
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

