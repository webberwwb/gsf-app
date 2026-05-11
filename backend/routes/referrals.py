from flask import Blueprint, jsonify, request, current_app
from models import db
from models.user import User, AuthToken
from models.referral_program import ReferralRecord
from models.order import Order
from models.credit_transaction import CreditTransaction
from services import referral_service

referrals_bp = Blueprint('referrals', __name__)

_TX_TYPE_LABELS = {
    'admin_grant': '管理员调整',
    'referral_invitee_bonus': '邀请好友成功下单',
    'referral_inviter_reward': '邀请好友成功下单',
    'order_spend': '订单使用',
    'order_credit_refund': '订单退回代金券',
}


def _require_user():
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
    user = User.query.get(auth_token.user_id)
    if not user or not user.is_active:
        return None, jsonify({'error': 'User not found or inactive'}), 401
    return user, None, None


@referrals_bp.route('/validate-code', methods=['GET'])
def validate_referral_code():
    """Debounced UI check: can current user bind this code (no mutation)."""
    user, err, code = _require_user()
    if err:
        return err, code
    raw = request.args.get('code') or request.args.get('referral_code') or ''
    ok, err_msg, meta = referral_service.validate_referral_code_for_bind(user, raw)
    if not ok:
        return jsonify({'valid': False, 'message': err_msg}), 200
    return jsonify({
        'valid': True,
        'inviter_nickname': meta['inviter_nickname'],
        'referral_code': meta['referral_code'],
    }), 200


@referrals_bp.route('/apply', methods=['POST'])
def apply_referral():
    user, err, code = _require_user()
    if err:
        return err, code
    data = request.get_json() or {}
    raw = data.get('code') or data.get('referral_code')
    if not raw:
        return jsonify({'error': '请输入推荐码'}), 400
    ok, msg = referral_service.try_bind_referral(user, raw)
    if not ok:
        return jsonify({'error': msg}), 400
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e, exc_info=True)
        return jsonify({'error': '保存失败', 'message': str(e)}), 500
    return jsonify({'user': user.to_dict(include_referrer=True), 'message': '推荐码已绑定'}), 200


@referrals_bp.route('/invitees', methods=['GET'])
def list_invitees():
    user, err, code = _require_user()
    if err:
        return err, code
    rows = ReferralRecord.query.filter_by(inviter_user_id=user.id).order_by(
        ReferralRecord.created_at.desc()
    ).all()
    out = []
    for r in rows:
        inv = User.query.get(r.invitee_user_id)
        label = '已发放奖励' if r.status == ReferralRecord.STATUS_REWARDED else '已绑定，未下单'
        if r.status != ReferralRecord.STATUS_REWARDED:
            has_order = Order.query.filter(
                Order.user_id == r.invitee_user_id,
                Order.deleted_at.is_(None),
            ).first() is not None
            if has_order:
                label = '已下单，待完成'
        out.append({
            'referral_id': r.id,
            'invitee_user_id': r.invitee_user_id,
            'invitee_nickname': inv.nickname if inv else None,
            'invitee_phone': (inv.phone[-4:] if inv and inv.phone else None),
            'status': r.status,
            'status_label': label,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'rewarded_at': r.rewarded_at.isoformat() if r.rewarded_at else None,
        })
    return jsonify({'invitees': out}), 200


@referrals_bp.route('/credit-transactions', methods=['GET'])
def list_my_credit_transactions():
    user, err, code = _require_user()
    if err:
        return err, code
    rows = (
        CreditTransaction.query.filter_by(user_id=user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(200)
        .all()
    )
    order_cache = {}
    out = []
    for t in rows:
        d = t.to_dict()
        d['tx_type_label'] = _TX_TYPE_LABELS.get(t.tx_type, t.tx_type)
        if t.related_order_id:
            if t.related_order_id not in order_cache:
                o = db.session.get(Order, t.related_order_id)
                order_cache[t.related_order_id] = o.order_number if o else None
            d['related_order_number'] = order_cache[t.related_order_id]
        else:
            d['related_order_number'] = None
        out.append(d)
    return jsonify({'transactions': out}), 200


@referrals_bp.route('/preview/<string:code>', methods=['GET'])
def preview(code):
    data = referral_service.invite_preview_for_code(code)
    if not data:
        return jsonify({'error': '邀请码无效'}), 404
    return jsonify(data), 200
