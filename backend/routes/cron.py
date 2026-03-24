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
from datetime import timedelta
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


@cron_bp.route('/cron/update-group-deal-statuses', methods=['POST'])
def update_group_deal_statuses_cron():
    """
    Daily cron job (00:01 EDT) to update group deal statuses:
    1. Mark deals as CLOSED when order_end_date has passed
    2. Mark deals as PREPARING on pickup day
    3. Mark deals as COMPLETED when one day after pickup_date
    
    This uses the same status update logic as the admin endpoint to ensure
    order statuses are cascaded correctly.
    
    Authentication: Requires X-Cron-Secret header
    """
    is_valid, error_response, status_code = verify_cron_request()
    if not is_valid:
        return error_response, status_code
    
    try:
        now = est_now()
        current_app.logger.info(f"[{now}] Running daily group deal status update...")
        
        deals_updated = []
        total_orders_updated = 0
        
        # ==============================================
        # Task 1: Mark deals as CLOSED when order_end_date passes
        # ==============================================
        current_app.logger.info("Task 1: Checking for deals to mark as CLOSED...")
        
        deals_to_close = GroupDeal.query.filter(
            GroupDeal.status == GroupDealStatus.ACTIVE.value,
            GroupDeal.order_end_date < now,
            GroupDeal.deleted_at.is_(None)
        ).all()
        
        for deal in deals_to_close:
            old_status = deal.status
            deal.status = GroupDealStatus.CLOSED.value
            deal.updated_at = now
            
            # Cascade to orders: All submitted orders become confirmed
            orders = Order.query.filter(
                Order.group_deal_id == deal.id,
                Order.status == OrderStatus.SUBMITTED.value,
                Order.status != OrderStatus.CANCELLED.value
            ).all()
            
            orders_updated = 0
            for order in orders:
                order.status = OrderStatus.CONFIRMED.value
                order.updated_at = now
                orders_updated += 1
            
            total_orders_updated += orders_updated
            deals_updated.append({
                'deal_id': deal.id,
                'title': deal.title,
                'old_status': old_status,
                'new_status': GroupDealStatus.CLOSED.value,
                'orders_updated': orders_updated
            })
            current_app.logger.info(f"  Closed deal '{deal.title}' (ID: {deal.id}), cascaded to {orders_updated} orders")
        
        if len(deals_to_close) > 0:
            current_app.logger.info(f"✅ Marked {len(deals_to_close)} deals as CLOSED")
        else:
            current_app.logger.info("ℹ️  No deals to mark as CLOSED")
        
        # ==============================================
        # Task 2: Mark deals as PREPARING on pickup day
        # ==============================================
        current_app.logger.info("Task 2: Checking for deals to mark as PREPARING...")
        
        # Get start and end of pickup day
        from datetime import datetime, time
        pickup_day_start = datetime.combine(now.date(), time.min)
        pickup_day_end = datetime.combine(now.date(), time.max)
        
        deals_to_prepare = GroupDeal.query.filter(
            GroupDeal.status == GroupDealStatus.CLOSED.value,
            GroupDeal.pickup_date >= pickup_day_start,
            GroupDeal.pickup_date <= pickup_day_end,
            GroupDeal.deleted_at.is_(None)
        ).all()
        
        for deal in deals_to_prepare:
            old_status = deal.status
            deal.status = GroupDealStatus.PREPARING.value
            deal.updated_at = now
            
            # Cascade to orders: All submitted/confirmed orders become preparing
            orders = Order.query.filter(
                Order.group_deal_id == deal.id,
                Order.status.in_([OrderStatus.SUBMITTED.value, OrderStatus.CONFIRMED.value]),
                Order.status != OrderStatus.CANCELLED.value
            ).all()
            
            orders_updated = 0
            for order in orders:
                order.status = OrderStatus.PREPARING.value
                order.updated_at = now
                orders_updated += 1
            
            total_orders_updated += orders_updated
            deals_updated.append({
                'deal_id': deal.id,
                'title': deal.title,
                'old_status': old_status,
                'new_status': GroupDealStatus.PREPARING.value,
                'orders_updated': orders_updated
            })
            current_app.logger.info(f"  Preparing deal '{deal.title}' (ID: {deal.id}), cascaded to {orders_updated} orders")
        
        if len(deals_to_prepare) > 0:
            current_app.logger.info(f"✅ Marked {len(deals_to_prepare)} deals as PREPARING")
        else:
            current_app.logger.info("ℹ️  No deals to mark as PREPARING")
        
        # ==============================================
        # Task 3: Mark deals as COMPLETED one day after pickup_date
        # ==============================================
        current_app.logger.info("Task 3: Checking for deals to mark as COMPLETED...")
        
        one_day_ago = now - timedelta(days=1)
        
        deals_to_complete = GroupDeal.query.filter(
            GroupDeal.status.in_([
                GroupDealStatus.CLOSED.value,
                GroupDealStatus.PREPARING.value,
                GroupDealStatus.READY_FOR_PICKUP.value
            ]),
            GroupDeal.pickup_date < one_day_ago,
            GroupDeal.deleted_at.is_(None)
        ).all()
        
        for deal in deals_to_complete:
            old_status = deal.status
            deal.status = GroupDealStatus.COMPLETED.value
            deal.updated_at = now
            
            deals_updated.append({
                'deal_id': deal.id,
                'title': deal.title,
                'old_status': old_status,
                'new_status': GroupDealStatus.COMPLETED.value,
                'orders_updated': 0
            })
            current_app.logger.info(f"  Completed deal '{deal.title}' (ID: {deal.id})")
        
        if len(deals_to_complete) > 0:
            current_app.logger.info(f"✅ Marked {len(deals_to_complete)} deals as COMPLETED")
        else:
            current_app.logger.info("ℹ️  No deals to mark as COMPLETED")
        
        # Commit all changes
        db.session.commit()
        
        # ==============================================
        # Return summary
        # ==============================================
        return jsonify({
            'success': True,
            'message': 'Hourly group deal status update completed',
            'deals_updated': len(deals_updated),
            'total_orders_updated': total_orders_updated,
            'updated_deals': deals_updated,
            'timestamp': now.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Error in hourly group deal status update: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to update group deal statuses',
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

