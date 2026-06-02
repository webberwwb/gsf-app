/** Align with backend Order.to_dict (consumer API). */

import { resolveOrderLineTotal } from './orderItemPricing'

export function orderItemsSubtotalNumber(order) {
  if (!order?.items?.length) return 0
  return order.items.reduce((sum, item) => sum + resolveOrderLineTotal(item), 0)
}

function orderTotalsFromItems(order) {
  if (!order?.items?.length) return false
  return orderItemsSubtotalNumber(order) > 0
}

export function orderSubtotalNumber(order) {
  if (!order) return 0
  const fromItems = orderItemsSubtotalNumber(order)
  if (orderTotalsFromItems(order)) return fromItems
  const fromField = Number(order.subtotal)
  return Number.isFinite(fromField) ? fromField : 0
}

export function orderTaxNumber(order) {
  if (!order) return 0
  const n = Number(order.tax)
  return Number.isFinite(n) ? n : 0
}

export function orderAdjustmentNumber(order) {
  if (!order) return 0
  const n = Number(order.adjustment_amount)
  return Number.isFinite(n) ? n : 0
}

export function orderShippingFeeNumber(order) {
  if (!order) return 0
  const n = Number(order.shipping_fee)
  return Number.isFinite(n) ? n : 0
}

export function orderTotalNumber(order) {
  if (!order) return 0
  const computed =
    orderSubtotalNumber(order) + orderTaxNumber(order) + orderShippingFeeNumber(order)
  if (orderTotalsFromItems(order)) {
    return computed > 0 ? computed : 0
  }
  const fromField = Number(order.total)
  if (Number.isFinite(fromField) && fromField > 0) return fromField
  if (computed > 0) return computed
  return Number.isFinite(fromField) ? fromField : 0
}

export function formatOrderMoney2(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0.00'
  return n.toFixed(2)
}

export function orderFinalTotalNumber(order) {
  if (!order) return 0
  const base = orderTotalNumber(order)
  const adj = orderAdjustmentNumber(order)
  const computed = base + adj
  if (orderTotalsFromItems(order)) {
    return computed > 0 ? computed : 0
  }
  if (order.final_total != null && order.final_total !== '') {
    const n = Number(order.final_total)
    if (Number.isFinite(n) && n > 0) return n
  }
  if (computed > 0) return computed
  const baseOnly = Number(order.total || 0)
  const adjOnly = Number(order.adjustment_amount || 0)
  const adjN = Number.isFinite(adjOnly) ? adjOnly : 0
  return Number.isFinite(baseOnly) ? baseOnly + adjN : 0
}

export function orderStoreCreditAppliedNumber(order) {
  if (!order) return 0
  const n = Number(order.store_credit_applied)
  return Number.isFinite(n) && n > 0 ? n : 0
}

export function orderAmountDueNumber(order) {
  if (!order) return 0
  const computed = orderFinalTotalNumber(order) - orderStoreCreditAppliedNumber(order)
  if (orderTotalsFromItems(order)) {
    return Math.max(0, computed)
  }
  if (order.amount_due != null && order.amount_due !== '') {
    const n = Number(order.amount_due)
    if (Number.isFinite(n) && n > 0) return Math.max(0, n)
  }
  return Math.max(0, computed)
}
