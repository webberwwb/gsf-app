"""
Constants API endpoints
Expose status enums to frontend
"""
from flask import Blueprint, jsonify
from constants.status_enums import OrderStatus, PaymentStatus, GroupDealStatus, UserStatus, DeliveryMethod
from utils.shipping import get_delivery_fee_config

constants_bp = Blueprint('constants', __name__, url_prefix='/api/constants')


@constants_bp.route('/order-statuses', methods=['GET'])
def get_order_statuses():
    """Get all order status values and labels"""
    return jsonify({
        'statuses': OrderStatus.get_all_labels()
    }), 200


@constants_bp.route('/payment-statuses', methods=['GET'])
def get_payment_statuses():
    """Get all payment status values and labels"""
    return jsonify({
        'statuses': PaymentStatus.get_all_labels()
    }), 200


@constants_bp.route('/group-deal-statuses', methods=['GET'])
def get_group_deal_statuses():
    """Get all group deal status values and labels"""
    return jsonify({
        'statuses': GroupDealStatus.get_all_labels(),
        'auto_managed': GroupDealStatus.get_auto_managed_statuses(),
        'manual_managed': GroupDealStatus.get_manual_managed_statuses()
    }), 200


@constants_bp.route('/user-statuses', methods=['GET'])
def get_user_statuses():
    """Get all user status values and labels"""
    return jsonify({
        'statuses': UserStatus.get_all_labels()
    }), 200


@constants_bp.route('/delivery-methods', methods=['GET'])
def get_delivery_methods():
    """Get all delivery method values and labels"""
    return jsonify({
        'methods': DeliveryMethod.get_all_labels()
    }), 200


@constants_bp.route('/delivery-fee-config', methods=['GET'])
def get_delivery_fee_config_public():
    """Get active delivery fee configuration (public endpoint)"""
    try:
        config = get_delivery_fee_config()
        
        if not config:
            # Return default values if no config exists
            return jsonify({
                'base_fee': 7.99,
                'threshold_1_amount': 58.00,
                'threshold_1_fee': 5.99,
                'threshold_2_amount': 128.00,
                'threshold_2_fee': 3.99,
                'threshold_3_amount': 150.00
            }), 200
        
        return jsonify({
            'base_fee': float(config.base_fee) if config.base_fee else 7.99,
            'threshold_1_amount': float(config.threshold_1_amount) if config.threshold_1_amount else 58.00,
            'threshold_1_fee': float(config.threshold_1_fee) if config.threshold_1_fee else 5.99,
            'threshold_2_amount': float(config.threshold_2_amount) if config.threshold_2_amount else 128.00,
            'threshold_2_fee': float(config.threshold_2_fee) if config.threshold_2_fee else 3.99,
            'threshold_3_amount': float(config.threshold_3_amount) if config.threshold_3_amount else 150.00
        }), 200
    except Exception as e:
        # Return defaults on error
        return jsonify({
            'base_fee': 7.99,
            'threshold_1_amount': 58.00,
            'threshold_1_fee': 5.99,
            'threshold_2_amount': 128.00,
            'threshold_2_fee': 3.99,
            'threshold_3_amount': 150.00
        }), 200


@constants_bp.route('/all', methods=['GET'])
def get_all_statuses():
    """Get all status enums"""
    return jsonify({
        'order': OrderStatus.get_all_labels(),
        'payment': PaymentStatus.get_all_labels(),
        'group_deal': {
            'statuses': GroupDealStatus.get_all_labels(),
            'auto_managed': GroupDealStatus.get_auto_managed_statuses(),
            'manual_managed': GroupDealStatus.get_manual_managed_statuses()
        },
        'user': UserStatus.get_all_labels(),
        'delivery_method': DeliveryMethod.get_all_labels()
    }), 200

