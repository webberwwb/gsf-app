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

export function nearestNeighborOrders(orders, depot, distanceKm) {
  const remaining = [...(orders || [])]
  const result = []
  let current = depot
  while (remaining.length) {
    let bestIndex = 0
    let bestDist = Infinity
    remaining.forEach((order, index) => {
      const coords = order?.address
        ? { lat: Number(order.address.latitude), lng: Number(order.address.longitude) }
        : null
      const located = coords && Number.isFinite(coords.lat) && Number.isFinite(coords.lng)
      const dist = located && current ? distanceKm(current, coords) : Number.POSITIVE_INFINITY
      if (dist < bestDist) {
        bestDist = dist
        bestIndex = index
      }
    })
    const [next] = remaining.splice(bestIndex, 1)
    result.push(next)
    const nextCoords = next?.address
      ? { lat: Number(next.address.latitude), lng: Number(next.address.longitude) }
      : null
    if (nextCoords && Number.isFinite(nextCoords.lat) && Number.isFinite(nextCoords.lng)) {
      current = nextCoords
    }
  }
  return result
}
