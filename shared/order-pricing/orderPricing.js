/**
 * Order money helpers (align with backend Order.to_dict and order_business_rules.py).
 * See shared/order-pricing/businessRules.js
 */

import { roundMoney, formatMoney } from './money.js'
import { resolveOrderLineTotal } from './orderItemPricing.js'
import { previewShippingFeeForOrder } from './shipping.js'

export { roundMoney, formatMoney, formatMoneyDisplay } from './money.js'

export function orderItemsSubtotalNumber(order, { deriveFromItems = false } = {}) {
  if (!order?.items?.length) return 0
  return roundMoney(order.items.reduce((sum, item) => sum + resolveOrderLineTotal(item), 0))
}

export function orderSubtotalNumber(order, { deriveFromItems = false } = {}) {
  if (!order) return 0
  const fromField = Number(order.subtotal)
  if (!deriveFromItems && Number.isFinite(fromField)) return roundMoney(fromField)
  return orderItemsSubtotalNumber(order)
}

export function orderShippingFeeNumber(order) {
  if (!order) return 0
  const n = Number(order.shipping_fee)
  return Number.isFinite(n) ? roundMoney(n) : 0
}

export function orderAdjustmentNumber(order) {
  if (!order) return 0
  const n = Number(order.adjustment_amount)
  return Number.isFinite(n) ? roundMoney(n) : 0
}

export function orderStoreCreditAppliedNumber(order) {
  if (!order) return 0
  const n = Number(order.store_credit_applied)
  return Number.isFinite(n) && n > 0 ? roundMoney(n) : 0
}

export function orderShippingTierBaseNumber(order, { creditOverride } = {}) {
  const subtotal = orderSubtotalNumber(order)
  const credit =
    creditOverride != null ? roundMoney(creditOverride) : orderStoreCreditAppliedNumber(order)
  const adjustment = orderAdjustmentNumber(order)
  return roundMoney(Math.max(0, subtotal - credit - adjustment))
}

export function orderTotalNumber(order, { deriveFromItems = false } = {}) {
  if (!order) return 0
  const fromField = Number(order.total)
  if (!deriveFromItems && Number.isFinite(fromField)) return roundMoney(fromField)
  return roundMoney(
    orderSubtotalNumber(order, { deriveFromItems }) +
      orderShippingFeeNumber(order) +
      orderAdjustmentNumber(order)
  )
}

export function orderFinalTotalNumber(order, opts = {}) {
  return orderTotalNumber(order, opts)
}

export function orderAmountDueNumber(order, { creditOverride, deriveFromItems = false } = {}) {
  if (!order) return 0
  if (!deriveFromItems && creditOverride == null && order.amount_due != null && order.amount_due !== '') {
    const n = Number(order.amount_due)
    if (Number.isFinite(n) && n >= 0) return roundMoney(n)
  }
  const subtotal = orderSubtotalNumber(order, { deriveFromItems })
  const credit =
    creditOverride != null ? roundMoney(creditOverride) : orderStoreCreditAppliedNumber(order)
  const adjustment = orderAdjustmentNumber(order)
  const shipping = orderShippingFeeNumber(order)
  return roundMoney(Math.max(0, subtotal - credit + adjustment + shipping))
}

/**
 * Live-edit preview for admin modal and confirm dialogs.
 * Pass `shippingConfig` (e.g. from delivery-fee-config API) to recalculate shipping
 * when items, weights, or delivery method change; omit to use `shippingFee` as-is.
 */
export function previewOrderTotals({
  items = [],
  deliveryMethod = 'pickup',
  shippingFee = 0,
  adjustment = 0,
  storeCredit = 0,
  shippingConfig
} = {}) {
  const subtotal = items.reduce((sum, item) => sum + resolveOrderLineTotal(item), 0)
  const credit = Number(storeCredit) || 0
  const adj = Number(adjustment) || 0
  const shipping =
    shippingConfig !== undefined
      ? previewShippingFeeForOrder({ items, deliveryMethod, shippingConfig })
      : deliveryMethod === 'delivery'
        ? Number(shippingFee) || 0
        : 0
  const amountDue = roundMoney(Math.max(0, subtotal - credit + adj + shipping))
  return {
    subtotal: roundMoney(subtotal),
    credit: roundMoney(credit),
    adjustment: roundMoney(adj),
    shipping: roundMoney(shipping),
    amountDue
  }
}

/** Alias for formatMoney — 2-decimal dollar string for templates. */
export function formatOrderMoney2(value) {
  return formatMoney(value)
}
