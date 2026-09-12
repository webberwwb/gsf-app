/** Display 我来送 in the driver's saved route order. Does not write seq. */

function routeSeqNumber(order) {
  const raw = order?.delivery_route_seq
  if (raw == null || raw === '') return null
  const seq = Number(raw)
  return Number.isFinite(seq) ? seq : null
}

export function sortSelfDeliveryOrders(orders) {
  return [...(orders || [])].sort((a, b) => {
    const aSeq = routeSeqNumber(a)
    const bSeq = routeSeqNumber(b)
    if (aSeq != null && bSeq != null && aSeq !== bSeq) return aSeq - bSeq
    if (aSeq != null && bSeq == null) return -1
    if (aSeq == null && bSeq != null) return 1
    return 0
  })
}

export function routeSeqLabel(order, index) {
  const seq = routeSeqNumber(order)
  return seq != null ? seq : index + 1
}
