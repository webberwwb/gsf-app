"""Referral program: bind invitee to inviter, issue codes on first completed order, inviter rewards."""
import secrets
from decimal import Decimal
from flask import current_app

from constants.status_enums import OrderStatus, UserStatus
from models import db
from models.user import User
from models.order import Order
from models.referral_program import ReferralProgramConfig, ReferralRecord
from models.base import utc_now
from services import credit_service


_REFERRAL_ALPHABET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'  # no 0,O,1,I

# Human-readable referral codes; DB column max 32 for headroom.
REFERRAL_CODE_LENGTH = 8


def get_active_referral_config():
    row = ReferralProgramConfig.query.filter_by(is_active=True).order_by(
        ReferralProgramConfig.id.desc()
    ).first()
    if not row:
        row = ReferralProgramConfig(
            invitee_bonus_amount=Decimal('5'),
            inviter_reward_amount=Decimal('5'),
            is_active=True,
        )
        db.session.add(row)
        db.session.flush()
    return row


def generate_unique_referral_code():
    """Allocate a new referral_code string, unique in users.referral_code (typically LENGTH chars)."""
    for _ in range(200):
        code = ''.join(
            secrets.choice(_REFERRAL_ALPHABET) for _ in range(REFERRAL_CODE_LENGTH)
        )
        if not User.query.filter_by(referral_code=code).first():
            return code
    raise RuntimeError('Could not allocate referral code')


def ensure_referral_code_for_user(user_id: int):
    """Assign referral_code if missing (call when user completes an order)."""
    user = User.query.filter_by(id=user_id).with_for_update().first()
    if not user:
        return None
    if user.referral_code:
        return user.referral_code
    user.referral_code = generate_unique_referral_code()
    db.session.flush()
    current_app.logger.info('Assigned referral code %s to user %s', user.referral_code, user_id)
    return user.referral_code


def normalize_referral_code(raw):
    if not raw:
        return None
    s = str(raw).strip().upper().replace('-', '').replace(' ', '')
    return s or None


def find_inviter_by_code(code_norm: str):
    if not code_norm:
        return None
    return User.query.filter_by(referral_code=code_norm).first()


def validate_referral_code_for_bind(invitee: User, raw_code: str):
    """
    Check whether invitee can bind this code (no DB writes).
    Returns (True, None, dict) with inviter_nickname, inviter User, or (False, error_zh, None).
    """
    code = normalize_referral_code(raw_code)
    if not code:
        return False, '请输入有效的推荐码', None

    if invitee.referred_by_user_id:
        return False, '您已使用过推荐码', None

    inviter = find_inviter_by_code(code)
    if not inviter or inviter.id == invitee.id:
        return False, '邀请码无效', None

    if inviter.status != UserStatus.ACTIVE.value:
        return False, '邀请码无效', None

    if not inviter.referral_code:
        return False, '邀请码无效', None

    cfg = get_active_referral_config()
    if not cfg.is_active:
        return False, '推荐活动未开放', None

    name = inviter.nickname or inviter.phone or '好友'
    return True, None, {'inviter': inviter, 'inviter_nickname': name, 'referral_code': inviter.referral_code}


def try_bind_referral(invitee: User, raw_code: str):
    """
    Bind invitee to inviter and credit invitee bonus. Returns (ok, error_message).
    error_message is Chinese for API.
    """
    ok, err, meta = validate_referral_code_for_bind(invitee, raw_code)
    if not ok:
        return False, err

    inviter = meta['inviter']
    cfg = get_active_referral_config()
    bonus = Decimal(str(cfg.invitee_bonus_amount or 0))
    if bonus < 0:
        bonus = Decimal('0')

    invitee.referred_by_user_id = inviter.id
    rec = ReferralRecord(
        inviter_user_id=inviter.id,
        invitee_user_id=invitee.id,
        status=ReferralRecord.STATUS_PENDING_ORDER,
    )
    db.session.add(rec)
    db.session.flush()

    if bonus > 0:
        tx = credit_service.apply_credit_change(
            invitee,
            bonus,
            credit_service.TX_REFERRAL_INVITEE,
            reason='好友推荐奖励',
            related_referral_id=rec.id,
            metadata={'inviter_id': inviter.id},
        )
        rec.invitee_bonus_transaction_id = tx.id
    db.session.flush()
    return True, None


def on_order_first_completed(order: Order, old_status: str):
    """
    When order becomes completed: ensure owner's referral code exists; pay inviter if applicable.
    """
    if old_status == OrderStatus.COMPLETED.value:
        return
    if order.status != OrderStatus.COMPLETED.value:
        return
    if order.deleted_at is not None:
        return

    ensure_referral_code_for_user(order.user_id)

    rec = ReferralRecord.query.filter_by(
        invitee_user_id=order.user_id,
        status=ReferralRecord.STATUS_PENDING_ORDER,
    ).with_for_update().first()

    if not rec:
        return

    cfg = get_active_referral_config()
    reward = Decimal(str(cfg.inviter_reward_amount or 0))
    if reward > 0:
        inviter = User.query.get(rec.inviter_user_id)
        if inviter:
            tx = credit_service.apply_credit_change(
                inviter,
                reward,
                credit_service.TX_REFERRAL_INVITER,
                reason='好友首单完成奖励',
                related_order_id=order.id,
                related_referral_id=rec.id,
                metadata={'invitee_id': order.user_id},
            )
            rec.inviter_reward_transaction_id = tx.id
    rec.status = ReferralRecord.STATUS_REWARDED
    rec.first_completed_order_id = order.id
    rec.rewarded_at = utc_now()
    db.session.flush()


def invite_preview_for_code(raw_code: str):
    """Public preview for share landing: inviter display name or None."""
    code = normalize_referral_code(raw_code)
    inviter = find_inviter_by_code(code)
    if not inviter or not inviter.referral_code:
        return None
    name = inviter.nickname or inviter.phone or '好友'
    return {'inviter_nickname': name, 'referral_code': inviter.referral_code}


def user_has_completed_order(user_id: int) -> bool:
    return db.session.query(Order.id).filter(
        Order.user_id == user_id,
        Order.status == OrderStatus.COMPLETED.value,
        Order.deleted_at.is_(None),
    ).first() is not None
