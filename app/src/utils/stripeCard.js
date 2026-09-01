export function cardLabel(brand, last4) {
  if (!last4) return ''
  const name = brand ? brand.charAt(0).toUpperCase() + brand.slice(1) : '卡'
  return `${name} •••• ${last4}`
}

export function hasSavedCard(userOrCard) {
  if (!userOrCard) return false
  return Boolean(userOrCard.has_card || userOrCard.has_card_on_file || userOrCard.stripe_payment_method_id)
}
