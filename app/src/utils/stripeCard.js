/** Shown next to bind-card so customers know we never store the full card. */
export const CARD_PRIVACY_NOTE =
  '卡号、有效期和安全码只在第三方支付平台（Stripe）加密托管，本APP不存储。我们仅保存用于扣款的加密编号，以及卡组织与卡号后四位（例如 Visa •••• 4242）方便您核对。'

export function cardLabel(brand, last4) {
  if (!last4) return ''
  const name = brand ? brand.charAt(0).toUpperCase() + brand.slice(1) : '卡'
  return `${name} •••• ${last4}`
}

export function hasSavedCard(userOrCard) {
  if (!userOrCard) return false
  return Boolean(userOrCard.has_card || userOrCard.has_card_on_file || userOrCard.stripe_payment_method_id)
}

export function orderCardLabel(order) {
  return cardLabel(order?.stripe_card_brand, order?.stripe_card_last4)
}

/** Customer-facing card / Stripe status for an order. */
export function customerPaymentDisplay(order) {
  if (!order) return { key: 'unpaid', label: '未支付' }
  if (order.payment_status === 'paid') return { key: 'paid', label: '已支付' }
  if (order.payment_method === 'card') {
    if (order.stripe_charge_status === 'failed') return { key: 'failed', label: '扣款失败' }
    if (
      order.stripe_payment_method_id
      || order.stripe_card_last4
      || order.stripe_charge_status === 'setup_complete'
    ) {
      return { key: 'ready', label: '已绑卡，待扣款' }
    }
    return { key: 'no_card', label: '未绑卡' }
  }
  return { key: 'unpaid', label: '未支付' }
}
