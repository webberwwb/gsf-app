"""
Cron job endpoints for GCP Cloud Scheduler
These endpoints are called by Cloud Scheduler to run scheduled tasks
"""
from flask import Blueprint, jsonify, request, current_app
from models import db
from models.order import Order
from models.groupdeal import GroupDeal
from models.base import est_now
from constants.status_enums import OrderStatus, GroupDealStatus
import os

cron_bp = Blueprint('cron', __name__)

# Secret key for authenticating cron requests (set in environment)
CRON_SECRET = os.environ.get('CRON_SECRET', 'your-secret-key-here')


def verify_cron_request():
    """Verify that the request is from Cloud Scheduler"""
    # Check for cron secret header
    auth_header = request.headers.get('X-Cron-Secret', '')
    if auth_header != CRON_SECRET:
        return False, jsonify({'error': 'Unauthorized'}), 401
    
    # Optional: Also verify Cloud Scheduler headers
    # cloud_scheduler_header = request.headers.get('X-CloudScheduler', '')
    # if not cloud_scheduler_header:
    #     return False, jsonify({'error': 'Not a Cloud Scheduler request'}), 401
    
    return True, None, None


@cron_bp.route('/cron/auto-confirm-orders', methods=['POST'])
def auto_confirm_orders_cron():
    """
    Daily cron job that runs at 00:00 EST to:
    1. Auto-confirm submitted orders where order_end_date has passed
    2. Update group deal statuses based on order dates
    
    Authentication: Requires X-Cron-Secret header
    """
    # Verify request is from Cloud Scheduler
    is_valid, error_response, status_code = verify_cron_request()
    if not is_valid:
        return error_response, status_code
    
    try:
        now = est_now()
        current_app.logger.info(f"[{now}] Running daily cron job...")
        
        # ==============================================
        # Task 1: Auto-confirm expired orders
        # ==============================================
        current_app.logger.info("Task 1: Auto-confirming expired orders...")
        
        orders_to_confirm = db.session.query(Order).join(
            GroupDeal, Order.group_deal_id == GroupDeal.id
        ).filter(
            Order.status == OrderStatus.SUBMITTED.value,
            GroupDeal.order_end_date < now
        ).all()
        
        confirmed_orders = []
        for order in orders_to_confirm:
            order.status = OrderStatus.CONFIRMED.value
            order.updated_at = now
            confirmed_orders.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'user_id': order.user_id,
                'group_deal_id': order.group_deal_id
            })
            current_app.logger.info(f"  Auto-confirmed order #{order.order_number} (ID: {order.id})")
        
        if len(confirmed_orders) > 0:
            current_app.logger.info(f"✅ Auto-confirmed {len(confirmed_orders)} orders")
        else:
            current_app.logger.info("ℹ️  No orders to confirm")
        
        # ==============================================
        # Task 2: Update group deal statuses
        # ==============================================
        current_app.logger.info("Task 2: Updating group deal statuses...")
        
        # Find all group deals that are not in final states
        active_deals = GroupDeal.query.filter(
            GroupDeal.status.in_(GroupDealStatus.get_auto_managed_statuses())
        ).all()
        
        updated_deals = []
        for deal in active_deals:
            old_status = deal.status
            new_status = None
            
            # Determine new status based on dates
            if deal.order_start_date > now:
                # Before order start date
                new_status = GroupDealStatus.UPCOMING.value
            elif deal.order_start_date <= now <= deal.order_end_date:
                # Within order window
                new_status = GroupDealStatus.ACTIVE.value
            elif deal.order_end_date < now:
                # Past order end date
                new_status = GroupDealStatus.CLOSED.value
            
            # Update if status changed
            if new_status and new_status != old_status:
                deal.status = new_status
                deal.updated_at = now
                updated_deals.append({
                    'deal_id': deal.id,
                    'title': deal.title,
                    'old_status': old_status,
                    'new_status': new_status
                })
                current_app.logger.info(f"  Updated deal '{deal.title}' (ID: {deal.id}): {old_status} → {new_status}")
        
        if len(updated_deals) > 0:
            current_app.logger.info(f"✅ Updated {len(updated_deals)} group deal statuses")
        else:
            current_app.logger.info("ℹ️  No group deal statuses to update")
        
        # Commit all changes
        db.session.commit()
        
        # ==============================================
        # Return summary
        # ==============================================
        return jsonify({
            'success': True,
            'message': f'Daily cron job completed',
            'orders_confirmed': len(confirmed_orders),
            'deals_updated': len(updated_deals),
            'confirmed_orders': confirmed_orders,
            'updated_deals': updated_deals,
            'timestamp': now.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Error in daily cron job: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to run daily cron job',
            'message': str(e)
        }), 500


@cron_bp.route('/cron/health', methods=['GET'])
def cron_health():
    """Health check endpoint for cron jobs"""
    return jsonify({
        'status': 'healthy',
        'service': 'cron-jobs',
        'timestamp': est_now().isoformat()
    }), 200

