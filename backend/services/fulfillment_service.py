"""Fulfillment (配货员) access, delivery assignment, timesheets, and earnings."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from math import ceil

from sqlalchemy.orm import joinedload, selectinload

from constants.status_enums import (
    DeliveryHandler,
    DeliveryMethod,
    GroupDealStatus,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from models import db
from models.base import est_now
from models.fulfillment import (
    FulfillmentPayout,
    FulfillmentProfile,
    FulfillmentSettlement,
    FulfillmentWorkSession,
    elapsed_minutes,
)
from models.groupdeal import GroupDeal
from models.order import Order, OrderItem
from models.user import User, UserRole


FULFILLABLE_DEAL_STATUSES = {
    GroupDealStatus.CLOSED.value,
    GroupDealStatus.PREPARING.value,
    GroupDealStatus.READY_FOR_PICKUP.value,
}

FULFILLMENT_STATUS_TRANSITIONS = {
    OrderStatus.PREPARING.value: {OrderStatus.PACKING_COMPLETE.value},
    OrderStatus.PACKING_COMPLETE.value: {
        OrderStatus.OUT_FOR_DELIVERY.value,
        OrderStatus.READY_FOR_PICKUP.value,
    },
    OrderStatus.OUT_FOR_DELIVERY.value: {
        OrderStatus.DELIVERED.value,
        OrderStatus.COMPLETED.value,
    },
    OrderStatus.DELIVERED.value: {OrderStatus.COMPLETED.value},
}

SEED_FULFILLMENT_EMAILS = (
    'forlove.dxy@gmail.com',
)

# Biweekly payday: every other Friday, starting 2026-09-11.
PAY_CYCLE_DAYS = 14
PAYDAY_ANCHOR = date(2026, 9, 11)
WEEKDAY_LABELS = ('周一', '周二', '周三', '周四', '周五', '周六', '周日')

NEARBY_DELIVERY_CITIES = ('markham', 'richmondhill')
NEARBY_DELIVERY_FEE = Decimal('6.00')
DEFAULT_DELIVERY_FEE = Decimal('7.00')


def biweekly_billing(today=None):
    today = today or est_now().date()
    days = (today - PAYDAY_ANCHOR).days
    cycles = ceil(days / PAY_CYCLE_DAYS) if days else 0
    next_pay = PAYDAY_ANCHOR + timedelta(days=cycles * PAY_CYCLE_DAYS)
    period_end = next_pay
    period_start = next_pay - timedelta(days=PAY_CYCLE_DAYS - 1)
    return {
        'cycle': 'biweekly',
        'cycle_label': '双周',
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        'next_pay_date': next_pay.isoformat(),
        'next_pay_weekday': WEEKDAY_LABELS[next_pay.weekday()],
        'is_payday': today == next_pay,
    }


def driver_cash_collected(order):
    """Cash the driver confirmed on delivery. Never inferred from payment_status."""
    amount = getattr(order, 'cash_collected_on_delivery', None)
    if amount is None:
        return Decimal('0')
    amount = Decimal(str(amount))
    return amount if amount > 0 else Decimal('0')


def record_driver_cash(order):
    """Record 代收现金 only when the driver marks 确认收款."""
    from utils.order_payment import mark_order_paid
    from utils.order_totals import calculate_amount_due

    if getattr(order, 'payment_method', None) != PaymentMethod.CASH.value:
        raise ValueError('仅现金订单可以标记已收款')
    if getattr(order, 'payment_status', None) == PaymentStatus.PAID.value:
        return order
    amount = calculate_amount_due(order)
    if amount <= 0:
        raise ValueError('没有需要代收的现金')
    if order.cash_collected_on_delivery is None:
        order.cash_collected_on_delivery = amount
    mark_order_paid(order)
    return order


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


_DEAL_STATUS_RANK = {
    GroupDealStatus.PREPARING.value: 0,
    GroupDealStatus.READY_FOR_PICKUP.value: 1,
    GroupDealStatus.CLOSED.value: 2,
    GroupDealStatus.ACTIVE.value: 3,
    GroupDealStatus.UPCOMING.value: 4,
    GroupDealStatus.COMPLETED.value: 5,
    GroupDealStatus.DRAFT.value: 6,
}


def _pickup_day(deal):
    picked = _as_date(getattr(deal, 'pickup_date', None))
    if isinstance(picked, datetime):
        return picked.date()
    return picked


def deal_for_work_date(work_date):
    """Group deal packed and delivered on this pickup day."""
    if isinstance(work_date, datetime):
        work_date = work_date.date()
    if not isinstance(work_date, date):
        return None
    start = datetime.combine(work_date, time.min)
    deals = GroupDeal.query.filter(
        GroupDeal.deleted_at.is_(None),
        GroupDeal.pickup_date >= start,
        GroupDeal.pickup_date < start + timedelta(days=1),
    ).all()
    if not deals:
        return None
    deals.sort(key=lambda deal: (_DEAL_STATUS_RANK.get(deal.status, 9), -deal.id))
    return deals[0]


def _settlement_deals(sessions, deliveries):
    ids = set()
    days = set()
    for session in sessions:
        if session.group_deal_id:
            ids.add(session.group_deal_id)
        elif session.work_date:
            days.add(session.work_date)
    for order in deliveries:
        if order.group_deal_id:
            ids.add(order.group_deal_id)

    deals = []
    known = set()
    if ids:
        for deal in GroupDeal.query.filter(
            GroupDeal.id.in_(ids),
            GroupDeal.deleted_at.is_(None),
        ).all():
            deals.append(deal)
            known.add(deal.id)
    if days:
        earliest, latest = min(days), max(days)
        extra = GroupDeal.query.filter(
            GroupDeal.deleted_at.is_(None),
            GroupDeal.pickup_date >= datetime.combine(earliest, time.min),
            GroupDeal.pickup_date < datetime.combine(latest + timedelta(days=1), time.min),
        ).all()
        for deal in extra:
            if deal.id not in known and _pickup_day(deal) in days:
                deals.append(deal)
                known.add(deal.id)
    return deals


def build_earnings_cycles(sessions, deliveries, payouts, today=None, rate_pair=None, settled_at_by_deal=None):
    """One settlement per group deal. Payouts are not tied to a deal."""
    del payouts
    today = today or est_now().date()
    deals = _settlement_deals(sessions, deliveries)
    by_id = {deal.id: deal for deal in deals}
    by_day = {}
    for deal in deals:
        by_day.setdefault(_pickup_day(deal), []).append(deal)

    def resolve_session_deal(session):
        linked = by_id.get(session.group_deal_id)
        if linked:
            return linked
        candidates = list(by_day.get(session.work_date) or [])
        if not candidates:
            return None
        candidates.sort(key=lambda deal: (_DEAL_STATUS_RANK.get(deal.status, 9), -deal.id))
        return candidates[0]

    buckets = {}

    def bucket_for(deal):
        key = deal.id if deal is not None else None
        if key not in buckets:
            pickup = _pickup_day(deal) if deal is not None else None
            buckets[key] = {
                'group_deal_id': deal.id if deal is not None else None,
                'group_deal_title': deal.title if deal is not None else None,
                'group_deal_status': deal.status if deal is not None else None,
                'group_deal_status_label': GroupDealStatus.get_label(deal.status) if deal is not None else None,
                'pickup_date': pickup.isoformat() if pickup else None,
                'pickup_sort': pickup,
                'is_current': bool(
                    deal is not None and (
                        deal.status == GroupDealStatus.PREPARING.value or pickup == today
                    )
                ),
                'labor': Decimal('0'),
                'delivery': Decimal('0'),
                'cash_collected': Decimal('0'),
                'hours': Decimal('0'),
                'delivery_count': 0,
                'sessions': [],
                'deliveries': [],
            }
        return buckets[key]

    for session in sessions:
        row = bucket_for(resolve_session_deal(session))
        row['labor'] += session.labor_amount or Decimal('0')
        row['hours'] += Decimal(str(session.hours or 0))
        row['sessions'].append(session.to_dict())
    for order in deliveries:
        row = bucket_for(by_id.get(order.group_deal_id))
        fee = Decimal(str(order.delivery_fee_earned or 0))
        cash = driver_cash_collected(order)
        row['delivery'] += fee
        row['cash_collected'] += cash
        row['delivery_count'] += 1
        row['deliveries'].append(_driver_fee_line(order, fee, cash_collected=cash, rate_pair=rate_pair))

    settled_at_by_deal = settled_at_by_deal or {}
    cycles = []
    ordered = sorted(
        buckets.values(),
        key=lambda row: (row['pickup_sort'] is None, -(row['pickup_sort'].toordinal() if row['pickup_sort'] else 0)),
    )
    for row in ordered:
        labor = row['labor']
        delivery = row['delivery']
        cash_collected = row['cash_collected']
        net = (labor + delivery - cash_collected).quantize(Decimal('0.01'))
        settled_at = settled_at_by_deal.get(row['group_deal_id'])
        settled = row['group_deal_id'] in settled_at_by_deal
        cycles.append({
            'group_deal_id': row['group_deal_id'],
            'group_deal_title': row['group_deal_title'],
            'group_deal_status': row['group_deal_status'],
            'group_deal_status_label': row['group_deal_status_label'],
            'pickup_date': row['pickup_date'],
            'is_current': row['is_current'],
            'settled': settled,
            'settled_at': settled_at,
            'sessions': row['sessions'],
            'deliveries': row['deliveries'],
            'totals': {
                'labor': float(labor),
                'delivery': float(delivery),
                'cash_collected': float(cash_collected),
                'paid': float(net) if settled else 0.0,
                'outstanding': 0.0 if settled else float(net),
                'hours': float(row['hours']),
                'delivery_count': row['delivery_count'],
            },
        })
    return cycles


def is_fulfillment_only(user):
    return bool(user and user.is_fulfillment and not user.is_admin)


def _city_key(city):
    return ''.join(ch for ch in (city or '').lower() if ch.isalnum())


def delivery_fee_for_address(address, nearby_fee=None, other_fee=None):
    city_key = _city_key(getattr(address, 'city', None))
    nearby = NEARBY_DELIVERY_FEE if nearby_fee is None else Decimal(str(nearby_fee))
    other = DEFAULT_DELIVERY_FEE if other_fee is None else Decimal(str(other_fee))
    if city_key in NEARBY_DELIVERY_CITIES:
        return nearby
    return other


def profile_region_fees(profile):
    """Driver region rates, falling back to the default schedule."""
    nearby = getattr(profile, 'nearby_fee', None) if profile is not None else None
    other = getattr(profile, 'other_fee', None) if profile is not None else None
    return (
        NEARBY_DELIVERY_FEE if nearby is None else Decimal(str(nearby)),
        DEFAULT_DELIVERY_FEE if other is None else Decimal(str(other)),
    )


def delivery_fee_rates(profile=None):
    nearby, other = profile_region_fees(profile)
    return {
        'nearby_cities': ['Markham', 'Richmond Hill'],
        'nearby_fee': float(nearby),
        'other_fee': float(other),
    }


def parse_rate(value):
    try:
        fee = Decimal(str(value)).quantize(Decimal('0.01'))
    except Exception:
        raise ValueError('请输入有效金额')
    if fee < 0:
        raise ValueError('费率不能为负数')
    return fee


def deal_is_fulfillable(deal):
    return bool(deal and deal.status in FULFILLABLE_DEAL_STATUSES)


def fulfillment_can_access_customer_addresses(actor, customer_id):
    """Admins always; 配货员 only if this customer has an order on a fulfillable deal."""
    if not actor:
        return False
    if not is_fulfillment_only(actor):
        return True
    found = (
        db.session.query(Order.id)
        .join(GroupDeal, Order.group_deal_id == GroupDeal.id)
        .filter(
            Order.user_id == customer_id,
            Order.deleted_at.is_(None),
            GroupDeal.deleted_at.is_(None),
            GroupDeal.status.in_(tuple(FULFILLABLE_DEAL_STATUSES)),
        )
        .first()
    )
    return bool(found)


def fulfillment_write_blocked(user, deal):
    """Return an error message if a fulfillment-only user cannot mutate this deal."""
    if not is_fulfillment_only(user):
        return None
    if not deal_is_fulfillable(deal):
        return '该团购已锁定，无法修改订单'
    return None


def fulfillment_status_allowed(old_status, new_status):
    allowed = FULFILLMENT_STATUS_TRANSITIONS.get(old_status, set())
    return new_status in allowed


def redact_user_public(user_dict):
    if not user_dict:
        return user_dict
    redacted = dict(user_dict)
    for key in ('phone', 'email', 'wechat', 'wechat_nickname', 'whatsapp_number'):
        if key in redacted:
            redacted[key] = None
    return redacted


def redact_address(address_dict):
    if not address_dict:
        return address_dict
    return {
        'id': address_dict.get('id'),
        'city': address_dict.get('city'),
        'country': address_dict.get('country'),
        'recipient_name': None,
        'phone': None,
        'address_line1': None,
        'address_line2': None,
        'postal_code': None,
        'delivery_instructions': None,
        'notification_email': None,
        'is_default': address_dict.get('is_default'),
    }


def apply_order_pii_lock(order_dict, deal, user):
    if not is_fulfillment_only(user):
        order_dict['pii_locked'] = False
        return order_dict
    if deal_is_fulfillable(deal):
        order_dict['pii_locked'] = False
        return order_dict
    if order_dict.get('user'):
        order_dict['user'] = redact_user_public(order_dict['user'])
    if order_dict.get('address'):
        order_dict['address'] = redact_address(order_dict['address'])
    order_dict['pii_locked'] = True
    return order_dict


def activate_profile_for_user(user_id):
    profile = FulfillmentProfile.query.filter_by(user_id=user_id).first()
    if profile:
        profile.is_active = True
        return profile
    profile = FulfillmentProfile(
        user_id=user_id,
        hourly_rate=Decimal('0'),
        delivery_fee_per_order=Decimal('0'),
        is_active=True,
    )
    db.session.add(profile)
    return profile


def deactivate_profile_for_user(user_id):
    profile = FulfillmentProfile.query.filter_by(user_id=user_id).first()
    if profile:
        profile.is_active = False
    return profile


def get_or_create_profile(user_id):
    profile = FulfillmentProfile.query.filter_by(user_id=user_id).first()
    if profile:
        return profile
    return activate_profile_for_user(user_id)


def parse_hhmm(value):
    if value is None or value == '':
        return None
    if isinstance(value, time):
        return value
    text = str(value).strip()
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError('时间格式应为 HH:MM')


def parse_work_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value), '%Y-%m-%d').date()


def compute_hours(start, end):
    minutes = elapsed_minutes(start, end, strict=True)
    return (minutes / Decimal('60')).quantize(Decimal('0.01'))


def snapshot_rate_for(user_id):
    profile = get_or_create_profile(user_id)
    return Decimal(str(profile.hourly_rate or 0))


def apply_session_hours(session):
    if session.end_time is None:
        session.hours = None
        return session
    session.hours = compute_hours(session.start_time, session.end_time)
    if session.hourly_rate_snapshot is None:
        session.hourly_rate_snapshot = snapshot_rate_for(session.user_id)
    return session


def open_session_for(user_id):
    return FulfillmentWorkSession.query.filter_by(user_id=user_id, end_time=None).first()


def clock_in(user_id, actor_id, notes=None, group_deal_id=None):
    existing = open_session_for(user_id)
    if existing:
        raise ValueError('已有未结束的工时，请先下班打卡')
    now = est_now()
    if group_deal_id is None:
        matched = deal_for_work_date(now.date())
        group_deal_id = matched.id if matched else None
    session = FulfillmentWorkSession(
        user_id=user_id,
        work_date=now.date(),
        start_time=now.time().replace(microsecond=0),
        end_time=None,
        notes=notes,
        group_deal_id=group_deal_id,
        hourly_rate_snapshot=snapshot_rate_for(user_id),
        created_by_user_id=actor_id,
        updated_by_user_id=actor_id,
    )
    db.session.add(session)
    return session


def clock_out(user_id, actor_id):
    session = open_session_for(user_id)
    if not session:
        raise ValueError('没有进行中的工时')
    now = est_now()
    session.end_time = now.time().replace(microsecond=0)
    session.updated_by_user_id = actor_id
    apply_session_hours(session)
    return session


def create_session(user_id, actor_id, payload):
    start = parse_hhmm(payload.get('start_time'))
    end = parse_hhmm(payload.get('end_time'))
    work_date = parse_work_date(payload.get('work_date') or est_now().date())
    if start is None:
        raise ValueError('开始时间不能为空')
    session = FulfillmentWorkSession(
        user_id=user_id,
        work_date=work_date,
        start_time=start,
        end_time=end,
        notes=payload.get('notes') or None,
        group_deal_id=payload.get('group_deal_id'),
        hourly_rate_snapshot=snapshot_rate_for(user_id),
        created_by_user_id=actor_id,
        updated_by_user_id=actor_id,
    )
    if session.group_deal_id is None:
        matched = deal_for_work_date(work_date)
        if matched:
            session.group_deal_id = matched.id
    apply_session_hours(session)
    db.session.add(session)
    return session


def update_session(session, actor_id, payload, allow_rate_edit=False):
    if 'work_date' in payload and payload.get('work_date'):
        session.work_date = parse_work_date(payload['work_date'])
    if 'start_time' in payload and payload.get('start_time'):
        session.start_time = parse_hhmm(payload['start_time'])
    if 'end_time' in payload:
        session.end_time = parse_hhmm(payload.get('end_time'))
    if 'notes' in payload:
        session.notes = payload.get('notes') or None
    if 'group_deal_id' in payload:
        session.group_deal_id = payload.get('group_deal_id')
    if allow_rate_edit and payload.get('hourly_rate_snapshot') is not None:
        session.hourly_rate_snapshot = Decimal(str(payload['hourly_rate_snapshot']))
    session.updated_by_user_id = actor_id
    apply_session_hours(session)
    return session


def list_fulfillment_staff():
    rows = (
        db.session.query(User, FulfillmentProfile)
        .join(UserRole, UserRole.user_id == User.id)
        .outerjoin(FulfillmentProfile, FulfillmentProfile.user_id == User.id)
        .filter(UserRole.role == 'fulfillment')
        .order_by(User.id.asc())
        .all()
    )
    staff = []
    for user, profile in rows:
        if profile is None:
            profile = activate_profile_for_user(user.id)
        staff.append({
            **profile.to_dict(),
            'user': {
                'id': user.id,
                'nickname': user.nickname,
                'email': user.email,
            },
        })
    return staff


def earnings_for_user(user_id, date_from=None, date_to=None):
    sessions_q = FulfillmentWorkSession.query.filter_by(user_id=user_id)
    payouts_q = FulfillmentPayout.query.filter_by(user_id=user_id)
    deliveries_q = Order.query.options(joinedload(Order.address)).filter(
        Order.deleted_at.is_(None),
        Order.delivery_method == DeliveryMethod.DELIVERY.value,
        Order.delivery_handler == DeliveryHandler.SELF.value,
        Order.delivery_assignee_id == user_id,
        Order.status.in_((OrderStatus.DELIVERED.value, OrderStatus.COMPLETED.value)),
    )

    if date_from:
        sessions_q = sessions_q.filter(FulfillmentWorkSession.work_date >= date_from)
        payouts_q = payouts_q.filter(FulfillmentPayout.paid_at >= datetime.combine(date_from, time.min))
        deliveries_q = deliveries_q.filter(Order.delivered_at >= datetime.combine(date_from, time.min))
    if date_to:
        sessions_q = sessions_q.filter(FulfillmentWorkSession.work_date <= date_to)
        payouts_q = payouts_q.filter(FulfillmentPayout.paid_at <= datetime.combine(date_to, time.max))
        end_to = datetime.combine(date_to, time.max)
        deliveries_q = deliveries_q.filter(
            db.or_(Order.delivered_at <= end_to, Order.delivered_at.is_(None))
        )

    sessions = sessions_q.order_by(
        FulfillmentWorkSession.work_date.desc(),
        FulfillmentWorkSession.start_time.desc(),
    ).all()
    payouts = payouts_q.order_by(FulfillmentPayout.paid_at.desc()).all()
    deliveries = deliveries_q.order_by(Order.delivered_at.desc(), Order.id.desc()).all()
    profile = get_or_create_profile(user_id)
    rate_pair = profile_region_fees(profile)

    labor_total = Decimal('0')
    for session in sessions:
        labor_total += session.labor_amount

    delivery_lines = []
    delivery_total = Decimal('0')
    cash_collected_total = Decimal('0')
    for order in deliveries:
        fee = Decimal(str(order.delivery_fee_earned or 0))
        cash = driver_cash_collected(order)
        delivery_total += fee
        cash_collected_total += cash
        deal = order.group_deal
        delivery_lines.append(_driver_fee_line(order, fee, deal, cash, rate_pair=rate_pair))

    paid_total = Decimal('0')
    for payout in payouts:
        paid_total += Decimal(str(payout.amount or 0))

    outstanding = (labor_total + delivery_total - cash_collected_total - paid_total).quantize(Decimal('0.01'))
    settlement_rows = FulfillmentSettlement.query.filter_by(user_id=user_id).all()
    settled_at_by_deal = {
        row.group_deal_id: row.settled_at.isoformat() if row.settled_at else None
        for row in settlement_rows
    }
    cycles = build_earnings_cycles(
        sessions, deliveries, payouts, rate_pair=rate_pair, settled_at_by_deal=settled_at_by_deal,
    )
    settled_paid = sum((Decimal(str(cycle['totals']['paid'])) for cycle in cycles), Decimal('0'))
    paid_total = (paid_total + settled_paid).quantize(Decimal('0.01'))
    outstanding = (outstanding - settled_paid).quantize(Decimal('0.01'))
    user = User.query.get(user_id)
    open_session = open_session_for(user_id)

    return {
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'email': user.email,
        } if user else None,
        'profile': profile.to_dict(),
        'delivery_fees': delivery_fee_rates(profile),
        'billing': biweekly_billing(),
        'cycles': cycles,
        'open_session': open_session.to_dict() if open_session else None,
        'sessions': [s.to_dict() for s in sessions],
        'deliveries': delivery_lines,
        'payouts': [p.to_dict() for p in payouts],
        'totals': {
            'labor': float(labor_total),
            'delivery': float(delivery_total),
            'cash_collected': float(cash_collected_total),
            'earned': float(labor_total + delivery_total),
            'paid': float(paid_total),
            'outstanding': float(outstanding),
            'hours': float(sum((s.hours or 0) for s in sessions)),
            'delivery_count': len(delivery_lines),
        },
    }


def set_cycle_settled(user_id, group_deal_id, settled, actor_id):
    row = FulfillmentSettlement.query.filter_by(
        user_id=user_id,
        group_deal_id=group_deal_id,
    ).first()
    if not settled:
        if row is not None:
            db.session.delete(row)
        return None
    if row is None:
        row = FulfillmentSettlement(
            user_id=user_id,
            group_deal_id=group_deal_id,
            settled_at=est_now(),
            settled_by_user_id=actor_id,
        )
        db.session.add(row)
    else:
        row.settled_at = est_now()
        row.settled_by_user_id = actor_id
    return row


def create_payout(user_id, actor_id, amount, notes=None, paid_at=None):
    payout = FulfillmentPayout(
        user_id=user_id,
        amount=Decimal(str(amount)),
        paid_at=paid_at or est_now(),
        notes=notes,
        paid_by_user_id=actor_id,
    )
    db.session.add(payout)
    return payout


def assign_delivery(order, handler, actor, third_party_note=None):
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        raise ValueError('仅配送订单可以分配')
    if handler not in DeliveryHandler.get_all_values():
        raise ValueError('无效的配送分配')
    order.delivery_handler = handler
    if handler == DeliveryHandler.SELF.value:
        order.delivery_assignee_id = actor.id
        order.third_party_note = None
    elif handler == DeliveryHandler.THIRD_PARTY.value:
        order.delivery_assignee_id = None
        order.third_party_note = (third_party_note or '').strip() or None
        order.delivery_route_seq = None
    else:
        order.delivery_assignee_id = None
        order.third_party_note = None
        order.delivery_route_seq = None
    return order


def set_route_order(deal_id, order_ids):
    orders = Order.query.filter(
        Order.group_deal_id == deal_id,
        Order.deleted_at.is_(None),
        Order.delivery_method == DeliveryMethod.DELIVERY.value,
        Order.id.in_(order_ids),
    ).all()
    by_id = {o.id: o for o in orders}
    seq = 1
    for order_id in order_ids:
        order = by_id.get(order_id)
        if not order or order.delivery_handler != DeliveryHandler.SELF.value:
            continue
        order.delivery_route_seq = seq
        seq += 1
    return seq - 1


def save_delivery_photo(order, photo_url):
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        raise ValueError('仅配送订单可以上传照片')
    url = (photo_url or '').strip()
    if not url:
        raise ValueError('请上传送达照片')
    order.delivery_photo_url = url
    return order


def clear_delivery_photo(order):
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        raise ValueError('仅配送订单可以删除照片')
    order.delivery_photo_url = None
    return order


def mark_delivered(order, actor, photo_url=None):
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        raise ValueError('仅配送订单可以标记送达')
    handler = order.delivery_handler or DeliveryHandler.UNASSIGNED.value
    if handler == DeliveryHandler.SELF.value:
        if not order.delivery_assignee_id:
            order.delivery_assignee_id = actor.id
        if order.delivery_fee_earned is None:
            assignee_id = order.delivery_assignee_id or actor.id
            nearby, other = profile_region_fees(get_or_create_profile(assignee_id))
            order.delivery_fee_earned = delivery_fee_for_address(order.address, nearby, other)
    if photo_url:
        order.delivery_photo_url = photo_url
    order.delivered_at = est_now()
    return order


def override_driver_delivery_fee(order, amount):
    if order.delivery_method != DeliveryMethod.DELIVERY.value:
        raise ValueError('仅配送订单可以更正司机配送费')
    if (order.delivery_handler or DeliveryHandler.UNASSIGNED.value) != DeliveryHandler.SELF.value:
        raise ValueError('仅自己配送的订单可以更正司机配送费')
    try:
        fee = Decimal(str(amount)).quantize(Decimal('0.01'))
    except Exception:
        raise ValueError('请输入有效金额')
    if fee < 0:
        raise ValueError('司机配送费不能为负数')
    order.delivery_fee_earned = fee
    return order


def _full_address(address):
    if not address:
        return None
    city_line = ', '.join(
        part for part in (getattr(address, 'city', None), getattr(address, 'postal_code', None)) if part
    )
    parts = [getattr(address, 'address_line1', None), getattr(address, 'address_line2', None), city_line or None]
    text = ', '.join(str(part).strip() for part in parts if part and str(part).strip())
    return text or None


def _driver_fee_line(order, fee, deal=None, cash_collected=None, rate_pair=None):
    from utils.order_totals import calculate_amount_due

    deal = deal if deal is not None else order.group_deal
    address = order.address
    if rate_pair is None:
        suggested = delivery_fee_for_address(address)
    else:
        suggested = delivery_fee_for_address(address, rate_pair[0], rate_pair[1])
    cash = driver_cash_collected(order) if cash_collected is None else cash_collected
    paid_on_delivery = cash > 0
    payment_label = '现金' if paid_on_delivery else (
        PaymentMethod.get_label(order.payment_method) if order.payment_method else None
    )
    paid_amount = cash if paid_on_delivery else calculate_amount_due(order)
    recipient = None
    if address and address.recipient_name:
        recipient = address.recipient_name
    elif order.user and order.user.nickname:
        recipient = order.user.nickname
    return {
        'order_id': order.id,
        'order_number': order.order_number,
        'group_deal_id': order.group_deal_id,
        'group_deal_title': deal.title if deal else None,
        'recipient_name': recipient,
        'address': _full_address(address),
        'city': address.city if address else None,
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'payment_method': order.payment_method,
        'payment_label': payment_label,
        'paid_amount': float(paid_amount),
        'fee': float(fee),
        'suggested_fee': float(suggested),
        'fee_overridden': fee != suggested,
        'cash_collected': float(cash),
    }


def deal_delivery_plan(deal, viewer):
    orders = (
        Order.query.options(
            joinedload(Order.user),
            selectinload(Order.address),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .filter(
            Order.group_deal_id == deal.id,
            Order.deleted_at.is_(None),
            Order.delivery_method == DeliveryMethod.DELIVERY.value,
            Order.status != OrderStatus.CANCELLED.value,
        )
        .order_by(Order.id.asc())
        .all()
    )
    orders.sort(key=_delivery_plan_sort_key)
    from utils.geocode import ensure_address_coords
    geocoded = 0
    for order in orders:
        if geocoded >= 80:
            break
        if order.address and (
            getattr(order.address, 'latitude', None) is None
            or getattr(order.address, 'longitude', None) is None
        ):
            before = (order.address.latitude, order.address.longitude)
            ensure_address_coords(order.address)
            if (order.address.latitude, order.address.longitude) != before:
                geocoded += 1
    if geocoded:
        db.session.commit()
    locked = is_fulfillment_only(viewer) and not deal_is_fulfillable(deal)
    buckets = {
        DeliveryHandler.UNASSIGNED.value: [],
        DeliveryHandler.SELF.value: [],
        DeliveryHandler.THIRD_PARTY.value: [],
    }
    for order in orders:
        payload = _delivery_order_payload(order, viewer, deal)
        handler = order.delivery_handler or DeliveryHandler.UNASSIGNED.value
        buckets.setdefault(handler, []).append(payload)
    return {
        'deal': {
            'id': deal.id,
            'title': deal.title,
            'status': deal.status,
            'pickup_date': deal.pickup_date.isoformat() if deal.pickup_date else None,
            'fulfillable': deal_is_fulfillable(deal),
            'pii_locked': locked,
        },
        'unassigned': buckets.get(DeliveryHandler.UNASSIGNED.value, []),
        'self': buckets.get(DeliveryHandler.SELF.value, []),
        'third_party': buckets.get(DeliveryHandler.THIRD_PARTY.value, []),
    }


def _postal_sort_key(order):
    raw = ''
    if order.address and order.address.postal_code:
        raw = order.address.postal_code
    return ''.join(ch for ch in raw.upper() if ch.isalnum()) or '\uffff'


def _delivery_plan_sort_key(order):
    postal = _postal_sort_key(order)
    if (order.delivery_handler or DeliveryHandler.UNASSIGNED.value) == DeliveryHandler.SELF.value:
        seq = order.delivery_route_seq
        return (0 if seq is not None else 1, seq if seq is not None else 0, postal)
    return (0, 0, postal)


def _delivery_order_payload(order, viewer, deal):
    from utils.order_totals import calculate_amount_due

    address = order.address.to_dict() if order.address else None
    user = None
    if order.user:
        user = {
            'id': order.user.id,
            'nickname': order.user.nickname,
            'phone': order.user.phone,
            'wechat': order.user.wechat,
        }
    items = []
    for item in order.items:
        name = item.product.name if item.product else f'商品{item.product_id}'
        items.append({
            'id': item.id,
            'name': name,
            'quantity': item.quantity,
            'variant_name': item.variant_name,
            'cutting': bool(getattr(item, 'cutting', False)),
        })
    payload = {
        'id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'payment_status': order.payment_status,
        'payment_method': order.payment_method,
        'final_total': float(order.total) if order.total is not None else 0.0,
        'amount_due': float(calculate_amount_due(order)),
        'cash_collected_on_delivery': float(order.cash_collected_on_delivery) if order.cash_collected_on_delivery is not None else None,
        'delivery_handler': order.delivery_handler or DeliveryHandler.UNASSIGNED.value,
        'delivery_assignee_id': order.delivery_assignee_id,
        'delivery_route_seq': order.delivery_route_seq,
        'delivery_photo_url': order.delivery_photo_url,
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'third_party_note': order.third_party_note,
        'notes': order.notes,
        'user': user,
        'address': address,
        'items': items,
        'items_count': len(items),
    }
    return apply_order_pii_lock(payload, deal, viewer)
