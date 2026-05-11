"""Store credit balance changes — all mutations should go through apply_credit_change."""
from decimal import Decimal
from flask import current_app

from models import db
from models.user import User
from models.credit_transaction import CreditTransaction

TX_ADMIN_GRANT = 'admin_grant'
TX_REFERRAL_INVITEE = 'referral_invitee_bonus'
TX_REFERRAL_INVITER = 'referral_inviter_reward'
TX_ORDER_SPEND = 'order_spend'
TX_ORDER_CREDIT_REFUND = 'order_credit_refund'


def apply_credit_change(
    user,
    delta,
    tx_type,
    *,
    reason=None,
    created_by_admin_user_id=None,
    related_order_id=None,
    related_referral_id=None,
    metadata=None,
):
    """
    Apply a delta to user.store_credit_balance and append CreditTransaction.
    delta may be negative; balance must not go below zero.
    """
    if not isinstance(delta, Decimal):
        delta = Decimal(str(delta))

    user_id = user.id
    # Reload balance from DB for consistency within concurrent requests
    row = User.query.filter_by(id=user_id).with_for_update().first()
    if not row:
        raise ValueError('User not found')

    bal = Decimal(str(row.store_credit_balance or 0))
    new_bal = bal + delta
    if new_bal < 0:
        raise ValueError('代金券余额不足')

    row.store_credit_balance = new_bal
    tx = CreditTransaction(
        user_id=user_id,
        delta=delta,
        balance_after=new_bal,
        tx_type=tx_type,
        reason=reason,
        metadata_json=metadata,
        created_by_admin_user_id=created_by_admin_user_id,
        related_order_id=related_order_id,
        related_referral_id=related_referral_id,
    )
    db.session.add(tx)
    db.session.flush()
    try:
        user.store_credit_balance = new_bal
    except Exception:
        pass
    current_app.logger.info(
        'credit tx user=%s type=%s delta=%s balance_after=%s',
        user_id, tx_type, delta, new_bal,
    )
    return tx


def refund_order_store_credit(order, user):
    """Return previously applied order credit to the user's balance."""
    from models.order import Order

    amt = order.store_credit_applied
    if amt is None or Decimal(str(amt)) <= 0:
        return None
    d = Decimal(str(amt))
    tx = apply_credit_change(
        user,
        d,
        TX_ORDER_CREDIT_REFUND,
        reason='订单修改退回代金券',
        related_order_id=order.id,
    )
    order.store_credit_applied = Decimal('0')
    return tx


def apply_order_store_credit_spend(user, order, amount):
    """Deduct store credit for an order; sets order.store_credit_applied."""
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    if amount <= 0:
        order.store_credit_applied = Decimal('0')
        return None
    tx = apply_credit_change(
        user,
        -amount,
        TX_ORDER_SPEND,
        reason='订单使用代金券',
        related_order_id=order.id,
    )
    order.store_credit_applied = amount
    return tx


def compute_max_credit_apply(user, order_pre_credit_final_total: Decimal):
    """Max credit that can apply to this order (bounded by balance and total)."""
    bal = Decimal(str(user.store_credit_balance or 0))
    cap = Decimal(str(order_pre_credit_final_total))
    return min(bal, cap) if cap > 0 else Decimal('0')
