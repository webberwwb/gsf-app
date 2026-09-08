"""推荐官 (influencer) program: profiles, lead bonus, commission accrual."""
from decimal import Decimal

from flask import current_app

from models import db
from models.base import utc_now
from models.influencer import (
    COMMISSION_PER_ITEM,
    COMMISSION_PER_WEIGHT,
    PAYOUT_CASH,
    PAYOUT_CREDIT,
    STATUS_CREDITED,
    STATUS_PAID,
    STATUS_PAYABLE,
    STATUS_REVERSED,
    InfluencerCommissionEntry,
    InfluencerProductRate,
    InfluencerProfile,
    InfluencerProgramConfig,
    InfluencerRateOverride,
)
from models.order import Order
from models.product import Product
from models.sdr import CommissionRule, SDR
from models.user import User, UserRole
from services import credit_service, referral_service
from utils.money import round_money


def ensure_default_global_rates():
    """Persist one global rate per product. Existing rows are never overwritten.

    If the table is empty, copy general-customer amounts from the first active
    SDR, then fill remaining products with 0. Later products also get 0.
    """
    existing = {row.product_id: row for row in InfluencerProductRate.query.all()}
    if not existing:
        sdr = SDR.query.filter_by(is_active=True).order_by(SDR.id.asc()).first()
        if sdr:
            for rule in CommissionRule.query.filter_by(sdr_id=sdr.id, is_active=True).all():
                amount = Decimal(str(rule.general_customer_amount or 0))
                if amount < 0:
                    amount = Decimal('0')
                commission_type = rule.commission_type or COMMISSION_PER_ITEM
                if commission_type not in (COMMISSION_PER_ITEM, COMMISSION_PER_WEIGHT):
                    commission_type = COMMISSION_PER_ITEM
                db.session.add(InfluencerProductRate(
                    product_id=rule.product_id,
                    commission_type=commission_type,
                    amount=amount,
                ))
            db.session.flush()
            existing = {row.product_id: row for row in InfluencerProductRate.query.all()}

    created = 0
    for product in Product.query.order_by(Product.id).all():
        if product.id in existing:
            continue
        db.session.add(InfluencerProductRate(
            product_id=product.id,
            commission_type=COMMISSION_PER_ITEM,
            amount=Decimal('0'),
        ))
        created += 1
    if created:
        db.session.flush()
    return created


def get_active_config():
    row = InfluencerProgramConfig.query.filter_by(is_active=True).order_by(
        InfluencerProgramConfig.id.desc()
    ).first()
    if not row:
        row = InfluencerProgramConfig(
            lead_bonus_amount=Decimal('5'),
            is_active=True,
        )
        db.session.add(row)
        db.session.flush()
    return row


def get_active_profile(user_id):
    if not user_id:
        return None
    return InfluencerProfile.query.filter_by(user_id=user_id, is_active=True).first()


def is_active_influencer(user):
    if not user:
        return False
    if not user.has_role('influencer'):
        return False
    profile = get_active_profile(user.id)
    return bool(profile)


def activate_profile_for_user(user_id):
    """Create or reactivate profile and ensure a referral code exists."""
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    if profile:
        profile.is_active = True
    else:
        profile = InfluencerProfile(
            user_id=user_id,
            payout_type=PAYOUT_CREDIT,
            is_active=True,
        )
        db.session.add(profile)
    referral_service.ensure_referral_code_for_user(user_id)
    ensure_default_global_rates()
    db.session.flush()
    return profile


def deactivate_profile_for_user(user_id):
    profile = InfluencerProfile.query.filter_by(user_id=user_id).first()
    if profile:
        profile.is_active = False
        db.session.flush()
    return profile


def convert_source_customers_to_influencer(owner_user_id, source, exclude_user_ids=None):
    """Bind customers of this source to a 推荐官 and stop matching SDR commission.

    Historical SDR records are left unchanged. Existing referred_by values are
    not overwritten. No past influencer commission is backfilled.
    """
    owner = User.query.get(owner_user_id)
    if not owner:
        raise ValueError('owner user not found')
    skip_ids = {owner.id}
    if exclude_user_ids:
        skip_ids.update(int(i) for i in exclude_user_ids)
    if not owner.has_role('influencer'):
        db.session.add(UserRole(user_id=owner.id, role='influencer'))
        db.session.flush()
        db.session.refresh(owner)
    activate_profile_for_user(owner.id)

    customers = User.query.filter(
        User.user_source == source,
        User.referred_by_user_id.is_(None),
        ~User.id.in_(skip_ids),
    ).all()
    bound_ids = []
    for customer in customers:
        customer.referred_by_user_id = owner.id
        bound_ids.append(customer.id)

    deactivated = []
    for sdr in SDR.query.filter_by(source_identifier=source, is_active=True).all():
        sdr.is_active = False
        deactivated.append(sdr.id)
    db.session.flush()
    return {
        'owner_user_id': owner.id,
        'bound_count': len(bound_ids),
        'bound_user_ids': bound_ids,
        'deactivated_sdr_ids': deactivated,
    }


def resolve_rate(influencer_user_id, product_id):
    """Return (commission_type, amount Decimal) or None if no positive rate."""
    override = InfluencerRateOverride.query.filter_by(
        influencer_user_id=influencer_user_id,
        product_id=product_id,
    ).first()
    if override is not None:
        amount = Decimal(str(override.amount or 0))
        if amount <= 0:
            return None
        return override.commission_type or COMMISSION_PER_ITEM, amount

    global_rate = InfluencerProductRate.query.filter_by(product_id=product_id).first()
    if global_rate is None:
        return None
    amount = Decimal(str(global_rate.amount or 0))
    if amount <= 0:
        return None
    return global_rate.commission_type or COMMISSION_PER_ITEM, amount


def _resolved_commission(influencer_user_id, product_id):
    """Rate lookup that still returns $0 rows so the UI can show type/unit."""
    override = InfluencerRateOverride.query.filter_by(
        influencer_user_id=influencer_user_id,
        product_id=product_id,
    ).first()
    if override is not None:
        return override.commission_type or COMMISSION_PER_ITEM, Decimal(str(override.amount or 0))
    global_rate = InfluencerProductRate.query.filter_by(product_id=product_id).first()
    if global_rate is None:
        return COMMISSION_PER_ITEM, Decimal('0')
    return global_rate.commission_type or COMMISSION_PER_ITEM, Decimal(str(global_rate.amount or 0))


def _product_weight_unit(product):
    pd = (product.pricing_data or {}) if product else {}
    return 'kg' if pd.get('unit') == 'kg' else 'lb'


def _reference_min_weight(product):
    """Same minimum-weight estimate as the customer app (getReferenceWeight)."""
    if not product:
        return None
    pt = product.pricing_type
    pd = product.pricing_data or {}
    if pt == 'bundled_weight':
        raw = pd.get('min_weight')
        try:
            weight = Decimal(str(raw if raw not in (None, '') else 7))
        except Exception:
            weight = Decimal('7')
        return weight if weight > 0 else Decimal('7')
    if pt == 'unit_weight':
        return Decimal('1')
    if pt == 'weight_range':
        mins = []
        for row in (pd.get('ranges') or []):
            try:
                mins.append(Decimal(str(row.get('min') or 0)))
            except Exception:
                continue
        return min(mins) if mins else None
    raw = pd.get('min_weight')
    if raw in (None, ''):
        return None
    try:
        weight = Decimal(str(raw))
    except Exception:
        return None
    return weight if weight > 0 else None


def _line_weight(item, product):
    if item.final_weight not in (None, ''):
        return Decimal(str(item.final_weight)), False
    ref = _reference_min_weight(product)
    if ref is None:
        return None, True
    qty = max(int(item.quantity or 1), 1)
    if product and product.pricing_type == 'weight_range':
        return ref, True
    return ref * qty, True


def _item_public_dict(item, product, influencer_user_id):
    commission_type, rate = _resolved_commission(influencer_user_id, item.product_id)
    weight, weight_estimated = _line_weight(item, product)
    if commission_type == COMMISSION_PER_WEIGHT:
        units = weight if weight is not None else Decimal('0')
        commission_estimated = weight_estimated or weight is None
        commission_unit = _product_weight_unit(product)
    else:
        units = Decimal(str(int(item.quantity or 0)))
        commission_estimated = False
        commission_unit = '件'
    commission_amount = round_money(rate * units)

    price_unit = '件'
    if product and product.pricing_type in ('unit_weight', 'bundled_weight'):
        price_unit = _product_weight_unit(product)
    unit_price = Decimal(str(item.unit_price or 0))
    line_total = Decimal(str(item.total_price or 0))
    is_weight_priced = bool(product and product.pricing_type in (
        'weight_range', 'unit_weight', 'bundled_weight',
    ))
    line_total_estimated = is_weight_priced and item.final_weight in (None, '')

    return {
        'product_id': item.product_id,
        'product_name': product.name if product else None,
        'variant_name': item.variant_name,
        'quantity': item.quantity,
        'pricing_type': product.pricing_type if product else None,
        'unit_price': float(round_money(unit_price)),
        'price_unit': price_unit,
        'line_total': float(round_money(line_total)),
        'line_total_estimated': line_total_estimated,
        'weight': float(weight) if weight is not None else None,
        'weight_estimated': bool(weight is not None and weight_estimated),
        'weight_unit': _product_weight_unit(product),
        'commission_type': commission_type,
        'commission_rate': float(round_money(rate)),
        'commission_unit': commission_unit,
        'commission_units': float(round_money(units)),
        'commission_amount': float(commission_amount),
        'commission_estimated': commission_estimated,
        'final_weight': float(item.final_weight) if item.final_weight is not None else None,
    }


def _apply_entry_details_to_items(items, entry):
    """Replace preview line commissions with the settled ledger breakdown."""
    leftover = list(entry.details or [])
    for row in items:
        match_idx = None
        for i, detail in enumerate(leftover):
            if detail.get('product_id') != row.get('product_id'):
                continue
            if detail.get('variant_name') not in (None, row.get('variant_name')):
                continue
            match_idx = i
            break
        if match_idx is None:
            continue
        detail = leftover.pop(match_idx)
        if detail.get('commission') is not None:
            row['commission_amount'] = float(round_money(Decimal(str(detail['commission']))))
        row['commission_estimated'] = False
        if detail.get('rate') is not None:
            row['commission_rate'] = float(round_money(Decimal(str(detail['rate']))))
        if detail.get('weight') is not None:
            weight = float(detail['weight'])
            row['weight'] = weight
            row['weight_estimated'] = False
            row['commission_units'] = weight
        elif detail.get('quantity') is not None:
            row['commission_units'] = float(detail['quantity'])
        if detail.get('commission_type'):
            row['commission_type'] = detail['commission_type']


def effective_rates_for_influencer(influencer_user_id):
    """All products with a resolved rate (global or override), including $0."""
    products = Product.query.filter_by(is_active=True).order_by(Product.sort_order, Product.id).all()
    overrides = {
        row.product_id: row
        for row in InfluencerRateOverride.query.filter_by(influencer_user_id=influencer_user_id).all()
    }
    globals_ = {
        row.product_id: row
        for row in InfluencerProductRate.query.all()
    }
    rows = []
    for product in products:
        override = overrides.get(product.id)
        global_rate = globals_.get(product.id)
        if override is not None:
            amount = Decimal(str(override.amount or 0))
            commission_type = override.commission_type or COMMISSION_PER_ITEM
            source = 'override'
        elif global_rate is not None:
            amount = Decimal(str(global_rate.amount or 0))
            commission_type = global_rate.commission_type or COMMISSION_PER_ITEM
            source = 'global'
        else:
            amount = Decimal('0')
            commission_type = COMMISSION_PER_ITEM
            source = 'global'
        rows.append({
            'product_id': product.id,
            'product_name': product.name,
            'pricing_type': product.pricing_type,
            'commission_type': commission_type,
            'commission_unit': 'lb' if commission_type == COMMISSION_PER_WEIGHT else '件',
            'amount': float(amount),
            'source': source,
        })
    return rows


def lead_bonus_for_inviter(inviter):
    """Amount to grant invitee when binding a 推荐官 code, or None to use friend bonus."""
    if not is_active_influencer(inviter):
        return None
    cfg = get_active_config()
    if not cfg.is_active:
        return Decimal('0')
    bonus = Decimal(str(cfg.lead_bonus_amount or 0))
    if bonus < 0:
        return Decimal('0')
    return bonus


def compute_order_commission(order, influencer_user_id):
    """Return (total Decimal, details list). Zero-rate products are omitted."""
    details = []
    total = Decimal('0')
    product_ids = [item.product_id for item in (order.items or [])]
    products = {
        p.id: p
        for p in Product.query.filter(Product.id.in_(product_ids)).all()
    } if product_ids else {}

    for item in order.items or []:
        if getattr(item, 'deleted_at', None):
            continue
        if getattr(item, 'cannot_fulfill', False):
            continue
        resolved = resolve_rate(influencer_user_id, item.product_id)
        if not resolved:
            continue
        commission_type, rate = resolved
        if commission_type == COMMISSION_PER_WEIGHT:
            weight = item.final_weight if item.final_weight else Decimal('0')
            line = round_money(rate * Decimal(str(weight)))
            qty = None
            weight_val = float(weight) if weight else 0
        else:
            qty = int(item.quantity or 0)
            line = round_money(rate * Decimal(qty))
            weight_val = None
        if line <= 0:
            continue
        product = products.get(item.product_id)
        details.append({
            'product_id': item.product_id,
            'product_name': product.name if product else None,
            'variant_name': item.variant_name,
            'commission_type': commission_type,
            'quantity': qty,
            'weight': weight_val,
            'rate': float(rate),
            'commission': float(line),
        })
        total += line
    return round_money(total), details


def _commission_from_group_deal_id(profile):
    raw = getattr(profile, 'commission_from_group_deal_id', None) if profile else None
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _order_settled_for_commission(order):
    from constants.status_enums import OrderStatus, PaymentStatus
    if order is None or getattr(order, 'deleted_at', None):
        return False
    if order.status == OrderStatus.CANCELLED.value:
        return False
    return (
        order.payment_status == PaymentStatus.PAID.value
        and order.status == OrderStatus.COMPLETED.value
    )


def accrue_for_order(order):
    """Create or refresh the ledger row when an order is paid and completed."""
    if order is None:
        return None
    if not _order_settled_for_commission(order):
        return InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()

    existing = InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()
    if existing:
        if existing.status == STATUS_REVERSED:
            profile = get_active_profile(existing.influencer_user_id)
            start_deal_id = _commission_from_group_deal_id(profile)
            if start_deal_id is not None and (order.group_deal_id or 0) < start_deal_id:
                return existing
            return _reaccrue_entry(existing, order)
        return _refresh_open_entry(existing, order)

    customer = User.query.get(order.user_id)
    if not customer or not customer.referred_by_user_id:
        return None
    if customer.referred_by_user_id == customer.id:
        return None

    profile = get_active_profile(customer.referred_by_user_id)
    if not profile:
        return None
    start_deal_id = _commission_from_group_deal_id(profile)
    if start_deal_id is not None and (order.group_deal_id or 0) < start_deal_id:
        return None
    influencer = User.query.get(profile.user_id)
    if not influencer or not influencer.has_role('influencer'):
        return None
    if influencer.id == order.user_id:
        return None

    amount, details = compute_order_commission(order, influencer.id)
    if amount <= 0:
        return None

    payout_type = profile.payout_type if profile.payout_type in (PAYOUT_CREDIT, PAYOUT_CASH) else PAYOUT_CREDIT
    entry = InfluencerCommissionEntry(
        influencer_user_id=influencer.id,
        customer_user_id=customer.id,
        order_id=order.id,
        amount=amount,
        payout_type=payout_type,
        status=STATUS_PAYABLE if payout_type == PAYOUT_CASH else STATUS_CREDITED,
        details=details,
    )
    db.session.add(entry)
    db.session.flush()

    if payout_type == PAYOUT_CREDIT:
        try:
            tx = credit_service.apply_credit_change(
                influencer,
                amount,
                credit_service.TX_INFLUENCER_COMMISSION,
                reason='推荐官收益',
                related_order_id=order.id,
                metadata={'customer_id': customer.id, 'entry_id': entry.id},
            )
            entry.credit_transaction_id = tx.id
            entry.status = STATUS_CREDITED
        except Exception as e:
            current_app.logger.error('influencer credit failed order=%s: %s', order.id, e, exc_info=True)
            entry.notes = '代金券入账失败，请管理员处理'
            entry.status = STATUS_PAYABLE
    db.session.flush()
    return entry


def _refresh_open_entry(entry, order):
    """Keep lifetime, balance, and line details in sync after reprice/weigh."""
    if entry.status in (STATUS_REVERSED, STATUS_PAID):
        return entry
    amount, details = compute_order_commission(order, entry.influencer_user_id)
    if amount <= 0:
        return reverse_for_order(order, reason='收益金额已变为0')

    old_amount = round_money(Decimal(str(entry.amount or 0)))
    new_amount = round_money(amount)
    entry.details = details
    if new_amount == old_amount:
        db.session.flush()
        return entry

    entry.amount = new_amount
    delta = new_amount - old_amount
    if entry.status == STATUS_CREDITED and delta != 0:
        influencer = User.query.get(entry.influencer_user_id)
        if influencer:
            try:
                tx_type = (
                    credit_service.TX_INFLUENCER_COMMISSION
                    if delta > 0
                    else credit_service.TX_INFLUENCER_COMMISSION_REVERSAL
                )
                tx = credit_service.apply_credit_change(
                    influencer,
                    delta,
                    tx_type,
                    reason='推荐官收益调整',
                    related_order_id=order.id,
                    metadata={
                        'customer_id': entry.customer_user_id,
                        'entry_id': entry.id,
                        'adjustment': True,
                    },
                )
                if delta > 0:
                    entry.credit_transaction_id = tx.id
            except ValueError:
                entry.notes = (entry.notes or '') + ' 调整失败：代金券余额不足'
                current_app.logger.warning(
                    'influencer refresh credit insufficient user=%s order=%s',
                    influencer.id,
                    order.id,
                )
            except Exception as e:
                current_app.logger.error(
                    'influencer refresh credit failed order=%s: %s', order.id, e, exc_info=True,
                )
    db.session.flush()
    return entry


def _reaccrue_entry(entry, order):
    """If a reversed entry's order is paid again, create a new accrual via a fresh row is not possible (unique order_id). Re-open instead."""
    if entry.status != STATUS_REVERSED:
        return entry
    profile = get_active_profile(entry.influencer_user_id)
    if not profile:
        return entry
    amount, details = compute_order_commission(order, entry.influencer_user_id)
    if amount <= 0:
        return entry
    entry.amount = amount
    entry.details = details
    entry.payout_type = profile.payout_type
    entry.notes = None
    influencer = User.query.get(entry.influencer_user_id)
    if profile.payout_type == PAYOUT_CREDIT and influencer:
        try:
            tx = credit_service.apply_credit_change(
                influencer,
                amount,
                credit_service.TX_INFLUENCER_COMMISSION,
                reason='推荐官收益',
                related_order_id=order.id,
                metadata={'customer_id': entry.customer_user_id, 'entry_id': entry.id, 'reaccrued': True},
            )
            entry.credit_transaction_id = tx.id
            entry.status = STATUS_CREDITED
        except Exception as e:
            current_app.logger.error('influencer reaccrue credit failed order=%s: %s', order.id, e, exc_info=True)
            entry.status = STATUS_PAYABLE
            entry.notes = '代金券入账失败，请管理员处理'
    else:
        entry.status = STATUS_PAYABLE
        entry.paid_at = None
        entry.paid_by_admin_id = None
    db.session.flush()
    return entry


def reverse_for_order(order, reason=None):
    """Reverse commission if order is unpaid/cancelled. Debit credit when possible."""
    if order is None:
        return None
    entry = InfluencerCommissionEntry.query.filter_by(order_id=order.id).first()
    if not entry or entry.status == STATUS_REVERSED:
        return entry

    if entry.status == STATUS_CREDITED and entry.amount and Decimal(str(entry.amount)) > 0:
        influencer = User.query.get(entry.influencer_user_id)
        if influencer:
            try:
                credit_service.apply_credit_change(
                    influencer,
                    -Decimal(str(entry.amount)),
                    credit_service.TX_INFLUENCER_COMMISSION_REVERSAL,
                    reason=reason or '推荐官收益冲回',
                    related_order_id=order.id,
                    metadata={'entry_id': entry.id},
                )
            except ValueError:
                entry.notes = (entry.notes or '') + ' 冲回失败：代金券余额不足'
                current_app.logger.warning(
                    'influencer reverse credit insufficient user=%s order=%s',
                    influencer.id,
                    order.id,
                )
    entry.status = STATUS_REVERSED
    db.session.flush()
    return entry


def mark_cash_paid(entry_ids, admin_user_id):
    now = utc_now()
    updated = []
    for entry_id in entry_ids:
        entry = InfluencerCommissionEntry.query.get(entry_id)
        if not entry or entry.status != STATUS_PAYABLE:
            continue
        if entry.payout_type != PAYOUT_CASH:
            continue
        entry.status = STATUS_PAID
        entry.paid_at = now
        entry.paid_by_admin_id = admin_user_id
        updated.append(entry)
    db.session.flush()
    return updated


def mask_wechat(value):
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    if len(s) <= 4:
        return s[0] + '***' if len(s) > 1 else '*'
    return s[:2] + '***' + s[-2:]


def customer_public_dict(user, extra=None):
    data = {
        'id': user.id,
        'nickname': user.nickname or f'用户{user.id}',
        'wechat_masked': mask_wechat(user.wechat),
    }
    if extra:
        data.update(extra)
    return data


def _is_closed_cycle_order(order):
    """Past group-buy cycles are closed; the current cycle stays in progress."""
    from constants.status_enums import GroupDealStatus, OrderStatus
    deal = getattr(order, 'group_deal', None)
    if deal is not None:
        return deal.status == GroupDealStatus.COMPLETED.value
    return order.status == OrderStatus.COMPLETED.value


def _visible_customer_orders(customer_ids, min_group_deal_id=None):
    from constants.status_enums import OrderStatus
    if not customer_ids:
        return []
    query = Order.query.filter(
        Order.user_id.in_(customer_ids),
        Order.deleted_at.is_(None),
        Order.status != OrderStatus.CANCELLED.value,
    )
    if min_group_deal_id is not None:
        query = query.filter(Order.group_deal_id >= int(min_group_deal_id))
    return query.order_by(Order.created_at.desc()).all()


def _paid_completed_orders(customer_ids, min_group_deal_id=None):
    from constants.status_enums import OrderStatus, PaymentStatus
    if not customer_ids:
        return []
    query = Order.query.filter(
        Order.user_id.in_(customer_ids),
        Order.deleted_at.is_(None),
        Order.status == OrderStatus.COMPLETED.value,
        Order.payment_status == PaymentStatus.PAID.value,
    )
    if min_group_deal_id is not None:
        query = query.filter(Order.group_deal_id >= int(min_group_deal_id))
    return query.all()


def dashboard_for(influencer_user_id):
    user = User.query.get(influencer_user_id)
    profile = get_active_profile(influencer_user_id)
    entries = InfluencerCommissionEntry.query.filter_by(
        influencer_user_id=influencer_user_id,
    ).all()
    credited = Decimal('0')
    payable = Decimal('0')
    paid_cash = Decimal('0')
    lifetime_earnings = Decimal('0')
    for entry in entries:
        if entry.status == STATUS_REVERSED:
            continue
        amt = Decimal(str(entry.amount or 0))
        lifetime_earnings += amt
        if entry.status == STATUS_CREDITED:
            credited += amt
        elif entry.status == STATUS_PAYABLE:
            payable += amt
        elif entry.status == STATUS_PAID:
            paid_cash += amt

    customers = User.query.filter_by(referred_by_user_id=influencer_user_id).all()
    customer_ids = [c.id for c in customers]
    orders = _paid_completed_orders(
        customer_ids,
        min_group_deal_id=_commission_from_group_deal_id(profile),
    )
    spend = sum((Decimal(str(order.total or 0)) for order in orders), Decimal('0'))
    store_credit = Decimal(str(user.store_credit_balance or 0)) if user else Decimal('0')
    # Remaining after cash settlement or spending store credit.
    account_balance = store_credit + payable

    payout_type = profile.payout_type if profile else PAYOUT_CREDIT
    return {
        'referral_code': user.referral_code if user else None,
        'payout_type': payout_type,
        'customer_count': len(customers),
        'order_count': len(orders),
        'customer_order_total': float(round_money(spend)),
        'lifetime_earnings': float(round_money(lifetime_earnings)),
        'account_balance': float(round_money(account_balance)),
        'customer_spend': float(round_money(spend)),
        'credited': float(round_money(credited)),
        'payable': float(round_money(payable)),
        'paid_cash': float(round_money(paid_cash)),
    }


def customers_for(influencer_user_id):
    profile = get_active_profile(influencer_user_id)
    min_deal_id = _commission_from_group_deal_id(profile)
    customers = User.query.filter_by(referred_by_user_id=influencer_user_id).order_by(
        User.creation_date.desc()
    ).all()
    customer_ids = [c.id for c in customers]
    orders_by_customer = {}
    for order in _visible_customer_orders(customer_ids, min_group_deal_id=min_deal_id):
        orders_by_customer.setdefault(order.user_id, []).append(order)
    paid_by_customer = {}
    for order in _paid_completed_orders(customer_ids, min_group_deal_id=min_deal_id):
        paid_by_customer.setdefault(order.user_id, []).append(order)
    rows = []
    for customer in customers:
        visible = orders_by_customer.get(customer.id, [])
        in_progress = sum(1 for o in visible if not _is_closed_cycle_order(o))
        closed = len(visible) - in_progress
        paid_orders = paid_by_customer.get(customer.id, [])
        spend = sum((Decimal(str(o.total or 0)) for o in paid_orders), Decimal('0'))
        commission = Decimal('0')
        for entry in InfluencerCommissionEntry.query.filter_by(
            influencer_user_id=influencer_user_id,
            customer_user_id=customer.id,
        ).all():
            if entry.status != STATUS_REVERSED:
                commission += Decimal(str(entry.amount or 0))
        rows.append(customer_public_dict(customer, {
            'order_count': len(visible),
            'in_progress_order_count': in_progress,
            'closed_order_count': closed,
            'paid_order_count': len(paid_orders),
            'spend': float(round_money(spend)),
            'commission': float(round_money(commission)),
        }))
    rows.sort(key=lambda row: (
        row['in_progress_order_count'] or 0,
        row['closed_order_count'] or 0,
    ), reverse=True)
    return rows


def customer_detail_for(influencer_user_id, customer_id):
    customer = User.query.get(customer_id)
    if not customer or customer.referred_by_user_id != influencer_user_id:
        return None
    profile = get_active_profile(influencer_user_id)
    min_deal_id = _commission_from_group_deal_id(profile)
    orders = _visible_customer_orders([customer.id], min_group_deal_id=min_deal_id)
    entries = {
        e.order_id: e
        for e in InfluencerCommissionEntry.query.filter_by(
            influencer_user_id=influencer_user_id,
            customer_user_id=customer.id,
        ).all()
    }
    product_ids = {
        item.product_id
        for order in orders
        for item in (order.items or [])
        if item.product_id
    }
    products = {
        p.id: p
        for p in Product.query.filter(Product.id.in_(product_ids)).all()
    } if product_ids else {}
    order_rows = []
    for order in orders:
        entry = entries.get(order.id)
        settled = entry is not None and entry.status != STATUS_REVERSED
        items = []
        preview = Decimal('0')
        any_estimated = False
        for item in order.items or []:
            row = _item_public_dict(item, products.get(item.product_id), influencer_user_id)
            items.append(row)
            preview += Decimal(str(row['commission_amount'] or 0))
            if row['commission_estimated'] or row['line_total_estimated']:
                any_estimated = True
        if settled:
            _apply_entry_details_to_items(items, entry)
            any_estimated = False
        deal = getattr(order, 'group_deal', None)
        closed = _is_closed_cycle_order(order)
        order_rows.append({
            'id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'payment_status': order.payment_status,
            'phase': 'closed' if closed else 'in_progress',
            'group_deal_id': order.group_deal_id,
            'group_deal_title': deal.title if deal else None,
            'subtotal': float(order.subtotal or 0),
            'total': float(order.total or 0),
            'totals_estimated': any_estimated,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'items': items,
            'commission': entry.to_dict() if settled else None,
            'estimated_commission': float(round_money(preview)),
        })
    return {
        'customer': customer_public_dict(customer),
        'orders': order_rows,
    }
