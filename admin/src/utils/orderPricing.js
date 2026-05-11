/** Order money helpers (align with backend Order.to_dict). */

export function orderFinalTotalNumber(order) {
  if (!order) return 0
  if (order.final_total != null && order.final_total !== '') {
    const n = Number(order.final_total)
    if (Number.isFinite(n)) return n
  }
  const base = Number(order.total || 0)
  const adj = Number(order.adjustment_amount || 0)
  const adjN = Number.isFinite(adj) ? adj : 0
  const sum = Number.isFinite(base) ? base + adjN : 0
  return sum
}

export function orderStoreCreditAppliedNumber(order) {
  if (!order) return 0
  const n = Number(order.store_credit_applied)
  return Number.isFinite(n) && n > 0 ? n : 0
}

export function orderAmountDueNumber(order) {
  if (!order) return 0
  if (order.amount_due != null && order.amount_due !== '') {
    const n = Number(order.amount_due)
    return Number.isFinite(n) ? Math.max(0, n) : 0
  }
  const finalT = orderFinalTotalNumber(order)
  const credit = orderStoreCreditAppliedNumber(order)
  return Math.max(0, finalT - credit)
}

export function formatOrderMoney2(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0.00'
  return n.toFixed(2)
}
