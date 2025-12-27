"""
Constants API endpoints
Expose status enums to frontend
"""
from flask import Blueprint, jsonify
from constants.status_enums import OrderStatus, PaymentStatus, GroupDealStatus, UserStatus, DeliveryMethod

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

