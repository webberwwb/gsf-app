const STORAGE_KEY = 'admin_group_deal_order_prefs'

const DEFAULTS = {
  activeOrderTab: 'pickup',
  showCompletedOrders: true,
  weightFilter: '',
  packingFilter: '',
  notesFilter: '',
  orderSort: 'payment',
  userSourceFilter: '',
  viewMode: 'card'
}

const VALID = {
  activeOrderTab: ['pickup', 'delivery', 'all'],
  weightFilter: ['', 'not_weighed', 'weighed'],
  packingFilter: ['', 'not_packed', 'packing_complete'],
  notesFilter: ['', 'has_notes', 'no_notes'],
  orderSort: ['payment', 'weight_asc', 'weight_desc', 'packing_asc', 'packing_desc'],
  userSourceFilter: ['', '花泽', 'default'],
  viewMode: ['card', 'list']
}

export function loadGroupDealOrderPrefs() {
  if (typeof localStorage === 'undefined') return { ...DEFAULTS }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULTS }
    const parsed = JSON.parse(raw)
    const result = { ...DEFAULTS }
    for (const key of Object.keys(DEFAULTS)) {
      const val = parsed[key]
      if (key === 'showCompletedOrders') {
        if (typeof val === 'boolean') result[key] = val
      } else if (VALID[key]?.includes(val)) {
        result[key] = val
      }
    }
    return result
  } catch {
    return { ...DEFAULTS }
  }
}

export function saveGroupDealOrderPrefs(prefs) {
  if (typeof localStorage === 'undefined') return
  try {
    const payload = {}
    for (const key of Object.keys(DEFAULTS)) {
      payload[key] = prefs[key] ?? DEFAULTS[key]
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // ignore quota / private mode errors
  }
}
