export function variantDealStockLimit(product, variantId) {
  if (variantId == null || !product) return null
  const variant = (product.variants || []).find((row) => String(row.id) === String(variantId))
  if (!variant || variant.deal_stock_limit === undefined || variant.deal_stock_limit === null || variant.deal_stock_limit === '') {
    return null
  }
  const limit = Number(variant.deal_stock_limit)
  return Number.isFinite(limit) ? limit : null
}

export function allVariantsSoldOut(product) {
  const variants = product?.variants || []
  if (!variants.length) return false
  const limits = variants.map((variant) => variantDealStockLimit(product, variant.id))
  if (limits.some((limit) => limit == null)) return false
  return limits.every((limit) => limit === 0)
}

export function variantStockMessage(limit) {
  if (limit == null) return ''
  if (limit <= 0) return '该规格已售罄'
  return `该规格库存不足，最多可选 ${limit} 件`
}
