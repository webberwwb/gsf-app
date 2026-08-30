"""
Canonical business rules for order pricing and points.

See ORDER_PRICING_AND_POINTS_RULES before changing order_item_pricing.py,
order_points.py, shipping.py, or frontend pricing mirrors.
"""

RULES_VERSION = '2026-08-25-deal'

ORDER_PRICING_AND_POINTS_RULES = """
ORDER PRICING AND POINTS RULES (v2026-08-24)
============================================

Change this text and RULES_VERSION when business rules change. Update tests and
shared/order-pricing/businessRules.js in the same PR.

TAX
---
All line prices are final shelf prices. orders.tax stays 0 in DB; never show or
calculate tax in UI, API, or helpers.

ORDER BREAKDOWN (display and calculation order)
-----------------------------------------------
1. subtotal           = sum(line.total_price)
2. store credit       = deducted from subtotal (代金券)
3. adjustment         = admin +/- amount (user app read-only)
4. shipping_fee       = delivery tier from shipping_tier_base (pickup = $0)
5. amount_due         = max(0, subtotal - credit + adjustment + shipping)

adjustment_discount = min(adjustment_amount, 0)   (negative admin discount only)
shipping_tier_base = max(0, subtotal - store_credit_applied + adjustment_discount)
Admin penalties (positive adjustment) do not reduce shipping tier base.
Admin discounts (negative adjustment) reduce shipping tier base.

Free-shipping tiers use shipping_tier_base allocated proportionally across lines.
Products with counts_toward_free_shipping=False are excluded from tier subtotal only.

Stored order.total = subtotal + shipping_fee + adjustment_amount (before credit).
amount_due = total - store_credit_applied (equivalent to formula above).

POINTS
------
1 point = $0.01 (cent). Award when admin marks order paid.
points = max(0, subtotal - store_credit_applied + adjustment_discount) * 100
Admin discounts (negative adjustment) reduce points; surcharges do not add points.
Shipping does not affect points. Do not backfill historical points balances.

LINE PRICING TYPES
------------------
per_item: unit from catalog schedule; total = unit_price * quantity.
  Quantity breaks (optional): pricing_data.quantity_breaks = [{min_qty, price}, ...].
  Highest min_qty with (pooled product qty on the order) >= min_qty wins.
  Pooled qty = sum of all variant lines of the same product on that order.
  variants_share_price=true (default): unit = break(product.price) + variant_delta.
  variants_share_price=false: unit = break(variant.price); each variant may have
  its own quantity_breaks. Mixed variants are separate order lines.

weight_range: band match weight >= min AND (max null OR weight < max).
  Estimate (no final_weight): unit_price = min(all band prices); qty=1 per line.
  Final: unit_price = matched band price; total = unit_price * 1

unit_weight: rate = price_per_unit + variant on rate.
  Estimate: total = rate * 1 lb per line; qty=1 per line.
  Final: total = rate * final_weight

bundled_weight: rate per lb; one 份 per line (qty=1).
  Estimate: total = rate * min_weight per line.
  Final: total = rate * final_weight (weight of that 份)

Weight-based products: user selects count N → N separate order lines (quantity=1 each).
Quantity breaks do not apply to weight pricing types.

DISCOUNT PRODUCTS
-----------------
Sale is per group-deal product (group_deal_products.is_discount), not a catalog-wide
flag. The same product can be on sale in one overlapping deal and list price in
another. Catalog sale_price / sale_price_per_unit / variant.sale_price are promo
amounts used only when that deal marks the product 本团折扣.
is_discount=true on a deal product pins it to the top of that deal's list (still
listed in its category). Out-of-stock items still sort last.
Customers see original + sale on that deal; order lines and points use the sale
(paid) amount. Quantity-break tiers still override the paid base when the pooled
qty matches. Catalog /products and Home 热门 always show list price.

SUBSTITUTES
-----------
accept_substitute=true + is_unavailable → substitute pricing model.
accept_substitute=false + is_unavailable → keep ORIGINAL price (pending admin).
cannot_fulfill=true → line total $0 (admin confirmed cannot supply).
Only cannot_fulfill zeros a declined line; not user preference alone.

User tooltip (不要备选): if original is unavailable we try to source it; if we
cannot supply the item is cancelled automatically. Cancellation may change order
total and delivery fee tier.

IMPLEMENTATION
--------------
All order mutations: recalculate lines → recalculate_order_totals → points preview.
Award points only in update_order_payment / pickup-cash complete handlers.
"""
