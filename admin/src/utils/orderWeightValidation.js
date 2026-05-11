/** Pricing types that require a positive final_weight for each line. */
export const WEIGHT_PRICING_TYPES = ['weight_range', 'unit_weight', 'bundled_weight']

/** Order statuses where missing final weight should trigger an extra warning (完成 / 配送中). */
export const STATUSES_WARN_IF_MISSING_FINAL_WEIGHT = ['completed', 'out_for_delivery', 'delivering']

export function pricingTypeNeedsFinalWeight(pricingType) {
  return WEIGHT_PRICING_TYPES.includes(pricingType)
}

export function isFinalWeightMissing(finalWeight) {
  if (finalWeight === null || finalWeight === undefined || finalWeight === '') return true
  const n = typeof finalWeight === 'number' ? finalWeight : parseFloat(finalWeight)
  return !Number.isFinite(n) || n <= 0
}

/**
 * One order line (API row or admin modal editable row with nested product).
 */
export function editableRowMissingFinalWeight(row) {
  if (!row?.product) return false
  if (!pricingTypeNeedsFinalWeight(row.product.pricing_type)) return false
  return isFinalWeightMissing(row.final_weight)
}

export function orderHasMissingFinalWeight(order) {
  if (!order?.items?.length) return false
  return order.items.some(editableRowMissingFinalWeight)
}

export function statusChangeWarnsIfMissingFinalWeight(status) {
  return STATUSES_WARN_IF_MISSING_FINAL_WEIGHT.includes(status)
}
