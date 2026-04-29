"""
Per-product repurchase rate from order line items (live query, not a cached report).

For each (user, product), non-cancelled orders that include the product are ordered in time.
All units in the chronologically first such order count as first purchase; all units in later
orders count as repurchase (回购).

repurchase_rate(product) = sum(repurchase units) / sum(all units) across eligible orders.
"""
from collections import defaultdict

from models import db
from models.order import Order, OrderItem
from models.product import Product
from constants.status_enums import OrderStatus


def compute_product_repurchase_rates(admin_user_ids=None):
    """
    Compute repurchase stats per product from current order data.

    Args:
        admin_user_ids: If provided, exclude these user_ids from the calculation
            (same spirit as other after-sales lists).

    Returns:
        list of dicts, each:
          product_id, product_name, total_sold_units, repurchase_units,
          repurchase_rate (float 0..1, or None if total_sold_units == 0)
        Sorted by repurchase_rate descending, then total_sold_units descending.
    """
    q = (
        db.session.query(
            Order.user_id,
            OrderItem.product_id,
            Order.id,
            Order.created_at,
            OrderItem.quantity,
            Product.name,
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(
            Order.deleted_at.is_(None),
            Order.status != OrderStatus.CANCELLED.value,
        )
    )
    if admin_user_ids:
        q = q.filter(~Order.user_id.in_(admin_user_ids))

    rows = q.all()

    # (user_id, product_id) -> order_id -> quantity sum for that line(s)
    by_user_product = defaultdict(lambda: defaultdict(int))
    # (user_id, product_id, order_id) -> created_at for sorting
    order_created = {}

    product_names = {}
    for user_id, product_id, order_id, created_at, quantity, name in rows:
        qty = int(quantity or 0)
        if qty <= 0:
            continue
        key = (user_id, product_id)
        by_user_product[key][order_id] += qty
        order_created[(user_id, product_id, order_id)] = created_at
        product_names[product_id] = name

    per_product_total = defaultdict(int)
    per_product_repurchase = defaultdict(int)

    for (user_id, product_id), order_qty in by_user_product.items():
        order_ids = list(order_qty.keys())
        order_ids.sort(
            key=lambda oid: (
                order_created.get((user_id, product_id, oid)).timestamp()
                if order_created.get((user_id, product_id, oid))
                else 0.0,
                oid,
            )
        )
        total_u = sum(order_qty.values())
        first_oid = order_ids[0]
        first_u = order_qty[first_oid]
        rep_u = total_u - first_u
        per_product_total[product_id] += total_u
        per_product_repurchase[product_id] += rep_u

    out = []
    for pid in per_product_total:
        total = per_product_total[pid]
        rep = per_product_repurchase[pid]
        rate = (rep / total) if total else None
        out.append(
            {
                'product_id': pid,
                'product_name': product_names.get(pid) or f'商品 #{pid}',
                'total_sold_units': total,
                'repurchase_units': rep,
                'repurchase_rate': rate,
            }
        )

    out.sort(
        key=lambda x: (
            -(x['repurchase_rate'] if x['repurchase_rate'] is not None else -1),
            -x['total_sold_units'],
            x['product_id'],
        )
    )
    return out
