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
)
from models import db
from models.base import est_now
from models.fulfillment import (
    FulfillmentPayout,
    FulfillmentProfile,
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
    'webberwwb@gmail.com',
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


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value


def build_earnings_cycles(sessions, deliveries, payouts, today=None):
    today = today or est_now().date()
    current = biweekly_billing(today)
    buckets = {}

    def bucket_for(day):
        info = biweekly_billing(day)
        key = info['period_end']
        if key not in buckets:
            buckets[key] = {
                'period_start': info['period_start'],
                'period_end': info['period_end'],
                'pay_date': info['next_pay_date'],
                'pay_weekday': info['next_pay_weekday'],
                'labor': Decimal('0'),
                'delivery': Decimal('0'),
                'paid': Decimal('0'),
                'hours': Decimal('0'),
                'delivery_count': 0,
            }
        return buckets[key]

    bucket_for(today)
    for session in sessions:
        row = bucket_for(session.work_date)
        row['labor'] += session.labor_amount or Decimal('0')
        row['hours'] += Decimal(str(session.hours or 0))
    for order in deliveries:
        row = bucket_for(_as_date(order.delivered_at) or today)
        row['delivery'] += Decimal(str(order.delivery_fee_earned or 0))
        row['delivery_count'] += 1
    for payout in payouts:
        row = bucket_for(_as_date(payout.paid_at) or today)
        row['paid'] += Decimal(str(payout.amount or 0))

    cycles = []
    for key in sorted(buckets, reverse=True):
        row = buckets[key]
        labor = row['labor']
        delivery = row['delivery']
        paid = row['paid']
        cycles.append({
            'period_start': row['period_start'],
            'period_end': row['period_end'],
            'pay_date': row['pay_date'],
            'pay_weekday': row['pay_weekday'],
            'is_current': key == current['period_end'],
            'totals': {
                'labor': float(labor),
                'delivery': float(delivery),
                'paid': float(paid),
                'outstanding': float((labor + delivery - paid).quantize(Decimal('0.01'))),
                'hours': float(row['hours']),
                'delivery_count': row['delivery_count'],
            },
        })
    return cycles


def is_fulfillment_only(user):
    return bool(user and user.is_fulfillment and not user.is_admin)


def _city_key(city):
    return ''.join(ch for ch in (city or '').lower() if ch.isalnum())


def delivery_fee_for_address(address):
    city_key = _city_key(getattr(address, 'city', None))
    if city_key in NEARBY_DELIVERY_CITIES:
        return NEARBY_DELIVERY_FEE
    return DEFAULT_DELIVERY_FEE


def delivery_fee_rates():
    return {
        'nearby_cities': ['Markham', 'Richmond Hill'],
        'nearby_fee': float(NEARBY_DELIVERY_FEE),
        'other_fee': float(DEFAULT_DELIVERY_FEE),
    }


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

    labor_total = Decimal('0')
    for session in sessions:
        labor_total += session.labor_amount

    delivery_lines = []
    delivery_total = Decimal('0')
    for order in deliveries:
        fee = Decimal(str(order.delivery_fee_earned or 0))
        delivery_total += fee
        deal = order.group_deal
        delivery_lines.append(_driver_fee_line(order, fee, deal))

    paid_total = Decimal('0')
    for payout in payouts:
        paid_total += Decimal(str(payout.amount or 0))

    outstanding = (labor_total + delivery_total - paid_total).quantize(Decimal('0.01'))
    profile = get_or_create_profile(user_id)
    user = User.query.get(user_id)
    open_session = open_session_for(user_id)

    return {
        'user': {
            'id': user.id,
            'nickname': user.nickname,
            'email': user.email,
        } if user else None,
        'profile': profile.to_dict(),
        'delivery_fees': delivery_fee_rates(),
        'billing': biweekly_billing(),
        'cycles': build_earnings_cycles(sessions, deliveries, payouts),
        'open_session': open_session.to_dict() if open_session else None,
        'sessions': [s.to_dict() for s in sessions],
        'deliveries': delivery_lines,
        'payouts': [p.to_dict() for p in payouts],
        'totals': {
            'labor': float(labor_total),
            'delivery': float(delivery_total),
            'earned': float(labor_total + delivery_total),
            'paid': float(paid_total),
            'outstanding': float(outstanding),
            'hours': float(sum((s.hours or 0) for s in sessions)),
            'delivery_count': len(delivery_lines),
        },
    }


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
            order.delivery_fee_earned = delivery_fee_for_address(order.address)
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


def _driver_fee_line(order, fee, deal=None):
    deal = deal if deal is not None else order.group_deal
    suggested = delivery_fee_for_address(order.address)
    return {
        'order_id': order.id,
        'order_number': order.order_number,
        'group_deal_id': order.group_deal_id,
        'group_deal_title': deal.title if deal else None,
        'city': order.address.city if order.address else None,
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
        'fee': float(fee),
        'suggested_fee': float(suggested),
        'fee_overridden': fee != suggested,
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
