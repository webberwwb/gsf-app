"""Record and query order operation audit trails."""
import json
from models import db
from models.order import Order, OrderItem
from models.order_audit import OrderAuditEvent
from models.product import Product
from models.base import utc_now


EVENT_MERGE = 'merge'
EVENT_ADMIN_ITEMS_REPLACE = 'admin_items_replace'
EVENT_CUSTOMER_ITEMS_REPLACE = 'customer_items_replace'


def _product_name(product_id):
    p = Product.query.get(product_id)
    return p.name if p else None


def item_snapshot(item, order_number=None):
    """JSON-serializable line snapshot for audit payloads."""
    if order_number is None and item.order_id:
        o = Order.query.get(item.order_id)
        order_number = o.order_number if o else None
    return {
        'item_id': item.id,
        'order_id': item.order_id,
        'order_number': order_number,
        'product_id': item.product_id,
        'product_name': _product_name(item.product_id),
        'quantity': item.quantity,
        'unit_price': float(item.unit_price) if item.unit_price is not None else None,
        'total_price': float(item.total_price) if item.total_price is not None else None,
        'final_weight': float(item.final_weight) if item.final_weight is not None else None,
        'variant_id': item.variant_id,
        'variant_name': item.variant_name,
        'accept_substitute': item.accept_substitute,
        'is_unavailable': bool(item.is_unavailable),
        'cannot_fulfill': bool(getattr(item, 'cannot_fulfill', False)),
        'source_order_id': getattr(item, 'source_order_id', None),
        'source_item_id': getattr(item, 'source_item_id', None),
        'deleted_at': item.deleted_at.isoformat() if getattr(item, 'deleted_at', None) else None,
    }


def active_items_for_order(order_id):
    return (
        OrderItem.query.filter(
            OrderItem.order_id == order_id,
            OrderItem.active(),
        ).all()
    )


def archived_items_for_order(order_id):
    return (
        OrderItem.query.filter(
            OrderItem.order_id == order_id,
            OrderItem.deleted_at.isnot(None),
        )
        .order_by(OrderItem.deleted_at.desc(), OrderItem.id.desc())
        .all()
    )


def record_order_audit(order_id, event_type, payload, actor_user_id=None, session=None):
    session = session or db.session
    event = OrderAuditEvent(
        order_id=order_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        payload=payload,
    )
    session.add(event)
    return event


def apply_item_sources_from_request(priced_items, order_id, request_items):
    """Link new lines to prior item ids when admin/customer sent item id."""
    by_id = {int(i['id']): i for i in request_items if i.get('id')}
    for priced in priced_items:
        rid = priced.get('_request_item_id')
        if rid and int(rid) in by_id:
            priced['source_order_id'] = order_id
            priced['source_item_id'] = int(rid)


def build_order_audit_trail(order_id):
    """Full trace: events, merge sources, archived lines, active line lineage."""
    order = Order.query.get(order_id)
    if not order:
        return None

    merged_from = (
        Order.query.filter_by(merged_into_order_id=order_id)
        .order_by(Order.created_at)
        .all()
    )
    merged_into = None
    if order.merged_into_order_id:
        merged_into = Order.query.get(order.merged_into_order_id)

    events = (
        OrderAuditEvent.query.filter_by(order_id=order_id)
        .order_by(OrderAuditEvent.created_at.desc(), OrderAuditEvent.id.desc())
        .all()
    )

    active = active_items_for_order(order_id)
    archived = archived_items_for_order(order_id)

    return {
        'order_id': order_id,
        'order_number': order.order_number,
        'merged_into': (
            {
                'id': merged_into.id,
                'order_number': merged_into.order_number,
                'merged_at': order.merged_at.isoformat() if order.merged_at else None,
            }
            if merged_into
            else None
        ),
        'merged_from_orders': [
            {
                'id': o.id,
                'order_number': o.order_number,
                'created_at': o.created_at.isoformat() if o.created_at else None,
                'deleted_at': o.deleted_at.isoformat() if o.deleted_at else None,
                'merged_at': o.merged_at.isoformat() if o.merged_at else None,
                'items': [
                    item_snapshot(i, o.order_number)
                    for i in OrderItem.query.filter_by(order_id=o.id).filter(
                        OrderItem.active()
                    ).all()
                ],
            }
            for o in merged_from
        ],
        'events': [e.to_dict() for e in events],
        'active_items': [item_snapshot(i, order.order_number) for i in active],
        'archived_items': [item_snapshot(i, order.order_number) for i in archived],
    }
