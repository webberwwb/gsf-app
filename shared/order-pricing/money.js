/**
 * Money amounts: round to 2 decimal places (half-up) for display and calculations.
 */

export function roundMoney(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return 0
  return Math.round((n + Number.EPSILON) * 100) / 100
}

/** Dollar string with exactly 2 decimals, e.g. "12.34" */
export function formatMoney(value) {
  return roundMoney(value).toFixed(2)
}

/** Display with $ prefix, e.g. "$12.34" */
export function formatMoneyDisplay(value) {
  return `$${formatMoney(value)}`
}
