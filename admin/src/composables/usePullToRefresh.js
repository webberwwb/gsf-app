import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const THRESHOLD = 72
const MAX_PULL = 120

function findScrollParent(el) {
  let node = el?.parentElement
  while (node && node !== document.body) {
    const { overflowY } = window.getComputedStyle(node)
    if (/(auto|scroll|overlay)/.test(overflowY) && node.scrollHeight > node.clientHeight) {
      return node
    }
    node = node.parentElement
  }
  return null
}

function isTouchDevice() {
  if (typeof window === 'undefined') return false
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

function shouldEnablePullToRefresh() {
  if (typeof window === 'undefined') return false
  const standalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  const narrowMobile = window.matchMedia('(max-width: 767px)').matches
  const coarsePointer = window.matchMedia('(pointer: coarse)').matches
  return (standalone || narrowMobile) && (coarsePointer || isTouchDevice())
}

const MIN_VISIBLE_PULL = 8

export function usePullToRefresh({ hostRef, onRefresh, isEnabled = () => true }) {
  const pullDistance = ref(0)
  const refreshing = ref(false)
  const enabled = ref(false)

  let scrollEl = null
  let startY = 0
  let tracking = false
  let touchHandlers = null

  const indicatorHeight = computed(() => {
    if (refreshing.value) return 56
    return Math.min(pullDistance.value, MAX_PULL)
  })

  const showIndicator = computed(() => pullDistance.value > MIN_VISIBLE_PULL || refreshing.value)

  const contentTransform = computed(() => {
    if (!showIndicator.value) return ''
    const offset = refreshing.value ? 56 : Math.min(pullDistance.value, MAX_PULL)
    return `translateY(${offset}px)`
  })

  const statusText = computed(() => {
    if (refreshing.value) return '刷新中...'
    if (pullDistance.value >= THRESHOLD) return '松开刷新'
    return '下拉刷新'
  })

  const readyToRefresh = computed(() => pullDistance.value >= THRESHOLD)

  function resetPull() {
    pullDistance.value = 0
    tracking = false
  }

  async function triggerRefresh() {
    if (refreshing.value || typeof onRefresh !== 'function') return
    refreshing.value = true
    pullDistance.value = THRESHOLD
    try {
      await onRefresh()
    } finally {
      refreshing.value = false
      resetPull()
    }
  }

  function onTouchStart(e) {
    if (!isEnabled() || refreshing.value || !scrollEl) return
    if (scrollEl.scrollTop > 0) return
    startY = e.touches[0].clientY
    tracking = true
  }

  function onTouchMove(e) {
    if (!tracking || refreshing.value || !scrollEl) return
    const currentY = e.touches[0].clientY
    const delta = currentY - startY
    if (delta <= 0) {
      resetPull()
      return
    }
    if (scrollEl.scrollTop > 0) {
      resetPull()
      return
    }
    e.preventDefault()
    pullDistance.value = Math.min(delta * 0.5, MAX_PULL)
  }

  function onTouchEnd() {
    if (!tracking) return
    if (pullDistance.value >= THRESHOLD) {
      triggerRefresh()
    } else {
      resetPull()
    }
  }

  function attach() {
    if (!hostRef.value) return
    scrollEl = hostRef.value.closest('.content-area') || findScrollParent(hostRef.value)
    if (!scrollEl) return

    enabled.value = true
    touchHandlers = {
      touchstart: onTouchStart,
      touchmove: onTouchMove,
      touchend: onTouchEnd,
      touchcancel: onTouchEnd
    }

    Object.entries(touchHandlers).forEach(([event, handler]) => {
      scrollEl.addEventListener(event, handler, { passive: event === 'touchmove' ? false : true })
    })
  }

  function detach() {
    if (!scrollEl || !touchHandlers) return
    Object.entries(touchHandlers).forEach(([event, handler]) => {
      scrollEl.removeEventListener(event, handler)
    })
    scrollEl = null
    touchHandlers = null
    enabled.value = false
    resetPull()
  }

  onMounted(() => {
    if (shouldEnablePullToRefresh()) {
      attach()
    }
  })

  onBeforeUnmount(detach)

  return {
    pullDistance,
    refreshing,
    enabled,
    showIndicator,
    indicatorHeight,
    contentTransform,
    statusText,
    readyToRefresh,
    triggerRefresh
  }
}
