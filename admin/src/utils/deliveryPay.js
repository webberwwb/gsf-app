import { formatOrderMoney2, orderAmountDueNumber } from './orderPricing'

/** Same rule as the printed delivery label: unpaid cash = collect on delivery. */
export function shouldCollectCash(order) {
  return order?.payment_method === 'cash' && order?.payment_status !== 'paid'
}

export function deliveryPayKind(order) {
  return shouldCollectCash(order) ? 'cash' : 'prepaid'
}

export function deliveryPayText(order) {
  if (shouldCollectCash(order)) {
    return `收现金 $${formatOrderMoney2(orderAmountDueNumber(order))}`
  }
  return order?.payment_method === 'cash' ? '不用收' : '线上支付'
}

export function cashDueSummary(orders = []) {
  const cashOrders = orders.filter(shouldCollectCash)
  const total = cashOrders.reduce((sum, order) => sum + orderAmountDueNumber(order), 0)
  return {
    count: cashOrders.length,
    total,
    text: cashOrders.length
      ? `应收现金 $${formatOrderMoney2(total)} · ${cashOrders.length} 单`
      : '不用收现金'
  }
}
