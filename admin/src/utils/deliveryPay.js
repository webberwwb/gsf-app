import { formatOrderMoney2, orderAmountDueNumber } from './orderPricing'

/** Same rule as the printed delivery label: unpaid cash = collect on delivery. */
export function shouldCollectCash(order) {
  return order?.payment_method === 'cash'
    && order?.payment_status !== 'paid'
    && orderAmountDueNumber(order) > 0
}

/** Only true when the driver tapped 确认收款. Paid cash is not enough. */
export function wasCashCollected(order) {
  return Number(order?.cash_collected_on_delivery) > 0
}

export function cashCollectedAmount(order) {
  return wasCashCollected(order) ? Number(order.cash_collected_on_delivery) : 0
}

export function deliveryPayKind(order) {
  if (shouldCollectCash(order)) return 'cash'
  if (wasCashCollected(order)) return 'collected'
  return 'prepaid'
}

export function deliveryPayText(order) {
  if (shouldCollectCash(order)) {
    return `收现金 $${formatOrderMoney2(orderAmountDueNumber(order))}`
  }
  if (wasCashCollected(order)) {
    return `已收现金 $${formatOrderMoney2(cashCollectedAmount(order))}`
  }
  const settled = order?.payment_status === 'paid'
    || order?.status === 'delivered'
    || order?.status === 'completed'
    || Boolean(order?.delivered_at)
  return settled ? '不用收' : '无需支付'
}

export function cashDueSummary(orders = []) {
  const dueOrders = orders.filter(shouldCollectCash)
  const collectedOrders = orders.filter(wasCashCollected)
  const dueTotal = dueOrders.reduce((sum, order) => sum + orderAmountDueNumber(order), 0)
  const collectedTotal = collectedOrders.reduce((sum, order) => sum + cashCollectedAmount(order), 0)
  const parts = []
  if (dueOrders.length) {
    parts.push(`收现金 $${formatOrderMoney2(dueTotal)} · ${dueOrders.length} 单`)
  }
  if (collectedOrders.length) {
    parts.push(`已收现金 $${formatOrderMoney2(collectedTotal)} · ${collectedOrders.length} 单`)
  }
  return {
    count: dueOrders.length,
    collectedCount: collectedOrders.length,
    total: dueTotal,
    collected: collectedTotal,
    text: parts.length ? parts.join(' · ') : '不用收现金'
  }
}
