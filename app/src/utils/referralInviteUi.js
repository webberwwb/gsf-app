import apiClient from '../api/client'

/** @type {Map<number, boolean>} userId -> has at least one completed order */
const completedOrderCache = new Map()

/**
 * Whether the user has any order with status `completed` (GET /orders), cached per user for the session.
 */
export async function getUserHasCompletedOrderCached(userId) {
  if (!userId) return false
  if (completedOrderCache.has(userId)) {
    return completedOrderCache.get(userId)
  }
  try {
    const { data } = await apiClient.get('/orders')
    const orders = data?.orders || []
    const has = orders.some((o) => o.status === 'completed')
    completedOrderCache.set(userId, has)
    return has
  } catch {
    completedOrderCache.set(userId, false)
    return false
  }
}

export function invalidateReferralInviteCompletedCache(userId) {
  if (userId != null) completedOrderCache.delete(userId)
}
