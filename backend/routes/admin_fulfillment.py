from datetime import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request

from models import db
from models.groupdeal import GroupDeal
from models.order import Order
from models.user import User
from constants.status_enums import OrderStatus, PaymentMethod, PaymentStatus
from routes.admin import require_admin_auth
from services import fulfillment_service
from utils.order_payment import mark_order_paid, maybe_complete_order
from services import influencer_service, referral_service

admin_fulfillment_bp = Blueprint('admin_fulfillment', __name__)


def _user(user_id):
    return User.query.get(user_id)


def _forbidden(message='没有权限'):
    return jsonify({'error': message}), 403


@admin_fulfillment_bp.route('/fulfillment/staff', methods=['GET'])
def list_staff():
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    if fulfillment_service.is_fulfillment_only(actor):
        profile = fulfillment_service.get_or_create_profile(actor.id)
        return jsonify({'staff': [profile.to_dict()]}), 200
    return jsonify({'staff': fulfillment_service.list_fulfillment_staff()}), 200


@admin_fulfillment_bp.route('/fulfillment/profiles/<int:target_user_id>', methods=['PUT'])
def update_profile(target_user_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    profile = fulfillment_service.get_or_create_profile(target_user_id)
    if 'hourly_rate' in data and data['hourly_rate'] is not None:
        profile.hourly_rate = data['hourly_rate']
    if 'delivery_fee_per_order' in data and data['delivery_fee_per_order'] is not None:
        profile.delivery_fee_per_order = data['delivery_fee_per_order']
    db.session.commit()
    return jsonify({'profile': profile.to_dict()}), 200


@admin_fulfillment_bp.route('/fulfillment/deals/<int:deal_id>/delivery-plan', methods=['GET'])
def get_delivery_plan(deal_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    deal = GroupDeal.query.filter(GroupDeal.id == deal_id, GroupDeal.deleted_at.is_(None)).first()
    if not deal:
        return jsonify({'error': '团购不存在'}), 404
    return jsonify(fulfillment_service.deal_delivery_plan(deal, _user(user_id))), 200


@admin_fulfillment_bp.route('/fulfillment/orders/<int:order_id>/assignment', methods=['PUT'])
def assign_order(order_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    deal = order.group_deal
    blocked = fulfillment_service.fulfillment_write_blocked(actor, deal)
    if blocked:
        return jsonify({'error': blocked}), 403
    data = request.get_json() or {}
    handler = (data.get('delivery_handler') or '').strip()
    try:
        fulfillment_service.assign_delivery(order, handler, actor, data.get('third_party_note'))
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'order': fulfillment_service._delivery_order_payload(order, actor, deal)}), 200


@admin_fulfillment_bp.route('/fulfillment/deals/<int:deal_id>/route', methods=['PUT'])
def save_route(deal_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    deal = GroupDeal.query.filter(GroupDeal.id == deal_id, GroupDeal.deleted_at.is_(None)).first()
    if not deal:
        return jsonify({'error': '团购不存在'}), 404
    blocked = fulfillment_service.fulfillment_write_blocked(actor, deal)
    if blocked:
        return jsonify({'error': blocked}), 403
    data = request.get_json() or {}
    order_ids = data.get('order_ids') or []
    if not isinstance(order_ids, list):
        return jsonify({'error': 'order_ids 必须是数组'}), 400
    fulfillment_service.set_route_order(deal_id, [int(i) for i in order_ids])
    db.session.commit()
    return jsonify(fulfillment_service.deal_delivery_plan(deal, actor)), 200


@admin_fulfillment_bp.route('/fulfillment/orders/<int:order_id>/photo', methods=['PUT'])
def save_delivery_photo(order_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    deal = order.group_deal
    blocked = fulfillment_service.fulfillment_write_blocked(actor, deal)
    if blocked:
        return jsonify({'error': blocked}), 403
    data = request.get_json() or {}
    try:
        fulfillment_service.save_delivery_photo(order, data.get('photo_url'))
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'order': fulfillment_service._delivery_order_payload(order, actor, deal)}), 200


@admin_fulfillment_bp.route('/fulfillment/orders/<int:order_id>/photo', methods=['DELETE'])
def delete_delivery_photo(order_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    deal = order.group_deal
    blocked = fulfillment_service.fulfillment_write_blocked(actor, deal)
    if blocked:
        return jsonify({'error': blocked}), 403
    try:
        fulfillment_service.clear_delivery_photo(order)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'order': fulfillment_service._delivery_order_payload(order, actor, deal)}), 200


@admin_fulfillment_bp.route('/fulfillment/orders/<int:order_id>/mark-delivered', methods=['POST'])
def mark_delivered(order_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    deal = order.group_deal
    blocked = fulfillment_service.fulfillment_write_blocked(actor, deal)
    if blocked:
        return jsonify({'error': blocked}), 403
    data = request.get_json() or {}
    photo_url = (data.get('photo_url') or '').strip() or None
    try:
        fulfillment_service.mark_delivered(order, actor, photo_url)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    old_status = order.status
    if order.payment_status == PaymentStatus.PAID.value:
        order.status = OrderStatus.COMPLETED.value
    else:
        order.status = OrderStatus.DELIVERED.value
    if order.payment_status == PaymentStatus.PAID.value:
        influencer_service.accrue_for_order(order)
    referral_service.on_order_first_completed(order, old_status)
    db.session.commit()
    return jsonify({'order': fulfillment_service._delivery_order_payload(order, actor, deal)}), 200


@admin_fulfillment_bp.route('/fulfillment/orders/<int:order_id>/mark-cash-received', methods=['POST'])
def mark_cash_received(order_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    deal = order.group_deal
    blocked = fulfillment_service.fulfillment_write_blocked(actor, deal)
    if blocked:
        return jsonify({'error': blocked}), 403
    if order.payment_method != PaymentMethod.CASH.value:
        return jsonify({'error': '仅现金订单可以标记已收款'}), 400
    if order.payment_status == PaymentStatus.PAID.value:
        old_status = order.status
        maybe_complete_order(order)
        referral_service.on_order_first_completed(order, old_status)
        influencer_service.accrue_for_order(order)
        db.session.commit()
        return jsonify({'order': fulfillment_service._delivery_order_payload(order, actor, deal)}), 200
    mark_order_paid(order)
    db.session.commit()
    return jsonify({'order': fulfillment_service._delivery_order_payload(order, actor, deal)}), 200


@admin_fulfillment_bp.route('/fulfillment/clock-status', methods=['GET'])
def clock_status():
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    session = fulfillment_service.open_session_for(user_id)
    return jsonify({'open_session': session.to_dict() if session else None}), 200


@admin_fulfillment_bp.route('/fulfillment/work-sessions/clock-in', methods=['POST'])
def clock_in():
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    target_id = user_id
    actor = _user(user_id)
    if actor.is_admin and data.get('user_id'):
        target_id = int(data['user_id'])
    try:
        session = fulfillment_service.clock_in(
            target_id, user_id, data.get('notes'), data.get('group_deal_id')
        )
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'session': session.to_dict()}), 200


@admin_fulfillment_bp.route('/fulfillment/work-sessions/clock-out', methods=['POST'])
def clock_out():
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    target_id = user_id
    actor = _user(user_id)
    if actor.is_admin and data.get('user_id'):
        target_id = int(data['user_id'])
    try:
        session = fulfillment_service.clock_out(target_id, user_id)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'session': session.to_dict()}), 200


@admin_fulfillment_bp.route('/fulfillment/work-sessions', methods=['POST'])
def create_session():
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    data = request.get_json() or {}
    target_id = user_id
    if actor.is_admin and data.get('user_id'):
        target_id = int(data['user_id'])
    elif fulfillment_service.is_fulfillment_only(actor) and data.get('user_id') and int(data['user_id']) != user_id:
        return _forbidden('只能为自己添加工时')
    try:
        session = fulfillment_service.create_session(target_id, user_id, data)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'session': session.to_dict()}), 201


@admin_fulfillment_bp.route('/fulfillment/work-sessions/<int:session_id>', methods=['PATCH'])
def update_session(session_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    from models.fulfillment import FulfillmentWorkSession
    session = FulfillmentWorkSession.query.get(session_id)
    if not session:
        return jsonify({'error': '工时记录不存在'}), 404
    if fulfillment_service.is_fulfillment_only(actor) and session.user_id != user_id:
        return _forbidden('只能修改自己的工时')
    data = request.get_json() or {}
    try:
        fulfillment_service.update_session(session, user_id, data, allow_rate_edit=actor.is_admin)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({'session': session.to_dict()}), 200


@admin_fulfillment_bp.route('/fulfillment/work-sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    from models.fulfillment import FulfillmentWorkSession
    session = FulfillmentWorkSession.query.get(session_id)
    if not session:
        return jsonify({'error': '工时记录不存在'}), 404
    if fulfillment_service.is_fulfillment_only(actor) and session.user_id != user_id:
        return _forbidden('只能删除自己的工时')
    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': '已删除'}), 200


@admin_fulfillment_bp.route('/fulfillment/orders/<int:order_id>/driver-fee', methods=['PUT'])
def override_driver_fee(order_id):
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    order = Order.query.filter(Order.id == order_id, Order.deleted_at.is_(None)).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    data = request.get_json() or {}
    if 'amount' not in data or data.get('amount') is None:
        return jsonify({'error': 'amount 必填'}), 400
    try:
        fulfillment_service.override_driver_delivery_fee(order, data.get('amount'))
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    return jsonify({
        'order_id': order.id,
        'delivery_fee_earned': float(order.delivery_fee_earned),
        'delivery': fulfillment_service._driver_fee_line(order, Decimal(str(order.delivery_fee_earned))),
    }), 200


@admin_fulfillment_bp.route('/fulfillment/earnings', methods=['GET'])
def get_earnings():
    user_id, error_response, status_code = require_admin_auth(allow_fulfillment=True)
    if error_response:
        return error_response, status_code
    actor = _user(user_id)
    target_id = request.args.get('user_id', type=int) or user_id
    if fulfillment_service.is_fulfillment_only(actor) and target_id != user_id:
        return _forbidden('只能查看自己的收入')
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    parsed_from = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    parsed_to = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
    return jsonify(fulfillment_service.earnings_for_user(target_id, parsed_from, parsed_to)), 200


@admin_fulfillment_bp.route('/fulfillment/payouts', methods=['POST'])
def create_payout():
    user_id, error_response, status_code = require_admin_auth()
    if error_response:
        return error_response, status_code
    data = request.get_json() or {}
    target_id = data.get('user_id')
    amount = data.get('amount')
    if not target_id or amount is None:
        return jsonify({'error': 'user_id 和 amount 必填'}), 400
    payout = fulfillment_service.create_payout(
        int(target_id), user_id, amount, data.get('notes'), None
    )
    db.session.commit()
    return jsonify({'payout': payout.to_dict()}), 201
