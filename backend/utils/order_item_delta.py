"""In-place customer item updates. Never wipe-and-replace the whole order."""
from models import db
from models.base import utc_now
from models.order import OrderItem
from utils.order_item_pricing import (
    create_order_item_rows,
    expand_request_items,
    priced_items_from_request,
    recalculate_existing_item,
)
from utils.query_batch import products_by_ids
from utils.stock_management import update_stock_after_order_modification


def apply_customer_item_delta(order, request_items, *, buyer_user_id):
    """Match request lines onto existing rows; insert/delete only the delta.

    Returns (changed: bool, error: str|None). Stock is adjusted by net summed qty.
    """
    if not request_items:
        return False, '请至少选择一个商品'

    existing = list(order.items)
    product_ids = [item.product_id for item in existing]
    product_ids.extend(item.get('product_id') for item in request_items)
    products = products_by_ids(product_ids)

    try:
        expanded = expand_request_items(request_items, products=products)
    except ValueError as e:
        return False, str(e)

    stock_ok, stock_err = update_stock_after_order_modification(
        order.group_deal_id, existing, expanded
    )
    if not stock_ok:
        return False, stock_err

    existing_by_id = {item.id: item for item in existing}
    unmatched = set(existing_by_id)
    kept = []
    new_request = []

    for req in expanded:
        src = _take_match(req, existing_by_id, unmatched)
        if src:
            kept.append((src, req))
        else:
            new_request.append(req)

    changed = bool(unmatched or new_request)
    affected_product_ids = set()

    for src, req in kept:
        new_qty = int(req.get('quantity') or 1)
        new_sub = req.get('accept_substitute')
        new_vid = req.get('variant_id')
        new_cut = bool(req.get('cutting'))
        if (
            int(src.quantity or 0) != new_qty
            or src.accept_substitute != new_sub
            or src.variant_id != new_vid
            or bool(getattr(src, 'cutting', False)) != new_cut
        ):
            changed = True
            src.quantity = new_qty
            if 'accept_substitute' in req:
                src.accept_substitute = new_sub
            if new_vid != src.variant_id:
                src.variant_id = new_vid
            if bool(getattr(src, 'cutting', False)) != new_cut:
                src.cutting = new_cut
                src.cutting_fee = None
            affected_product_ids.add(src.product_id)

    if unmatched:
        changed = True
        for item_id in unmatched:
            affected_product_ids.add(existing_by_id[item_id].product_id)
        now = utc_now()
        OrderItem.query.filter(OrderItem.id.in_(list(unmatched))).update(
            {'deleted_at': now},
            synchronize_session=False,
        )

    if new_request:
        for req in new_request:
            if req.get('product_id'):
                affected_product_ids.add(req['product_id'])
        try:
            priced, _ = priced_items_from_request(
                new_request,
                group_deal_id=order.group_deal_id,
                buyer_user_id=buyer_user_id,
            )
        except ValueError as e:
            return False, str(e)
        create_order_item_rows(order.id, priced, db.session)

    db.session.flush()
    db.session.expire(order, ['items'])
    if affected_product_ids:
        for item in order.items:
            if item.product_id in affected_product_ids:
                recalculate_existing_item(item)
    return changed, None


def _take_match(req, existing_by_id, unmatched):
    req_id = req.get('id')
    if req_id and req_id in unmatched:
        src = existing_by_id.get(req_id)
        if (
            src
            and src.product_id == req.get('product_id')
            and src.variant_id == req.get('variant_id')
            and bool(getattr(src, 'cutting', False)) == bool(req.get('cutting'))
        ):
            unmatched.discard(src.id)
            return src

    pid = req.get('product_id')
    vid = req.get('variant_id')
    want_cut = bool(req.get('cutting'))
    candidates = [
        existing_by_id[item_id]
        for item_id in unmatched
        if existing_by_id[item_id].product_id == pid
        and existing_by_id[item_id].variant_id == vid
        and bool(getattr(existing_by_id[item_id], 'cutting', False)) == want_cut
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda item: (0 if item.final_weight else 1, item.id))
    src = candidates[0]
    unmatched.discard(src.id)
    return src
