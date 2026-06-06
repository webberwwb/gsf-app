/** Points preview (mirrors backend/utils/order_points.py). */

import { roundMoney } from './money.js'
import {
  orderSubtotalNumber,
  orderStoreCreditAppliedNumber,
  orderAdjustmentNumber
} from './orderPricing.js'

export function calculateOrderPoints(order) {
  if (!order) return 0
  const subtotal = orderSubtotalNumber(order)
  const credit = orderStoreCreditAppliedNumber(order)
  const adjustment = orderAdjustmentNumber(order)
  const discount = adjustment < 0 ? adjustment : 0
  return Math.max(0, Math.floor(roundMoney(subtotal - credit + discount) * 100))
}
