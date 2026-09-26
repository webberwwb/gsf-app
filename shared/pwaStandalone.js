// iOS home-screen web apps (especially after recent iOS updates) open a real
// <a href> in an in-app browser — URL bar, back, refresh — even for same-origin
// routes. Vue router-link renders those anchors. Cancel that gesture and route
// with the history API so the installed app stays fullscreen.
//
// This runs everywhere, not just when standalone mode is detected: an icon that
// iOS already launched with browser chrome reports itself as non-standalone, and
// those are exactly the installs that need rescuing. Elsewhere it is equivalent
// to the SPA routing the links already perform.

function closestAnchor(node) {
  if (!node || node === document || node === window) return null
  const el = node.nodeType === 1 ? node : node.parentElement
  return el?.closest?.('a') || null
}

function currentPath() {
  return `${window.location.pathname}${window.location.search}${window.location.hash}`
}

function pathOf(url) {
  return `${url.pathname}${url.search}${url.hash}`
}

function hasModifier(event) {
  return Boolean(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
}

function readAppUrl(anchor) {
  if (!anchor || anchor.hasAttribute('download')) return null
  if (anchor.target && anchor.target !== '_self') return null
  const raw = anchor.dataset.pwaHref || anchor.getAttribute('href')
  if (!raw || /^(mailto:|tel:|sms:|javascript:)/i.test(raw)) return null
  if (raw.startsWith('#') && !raw.startsWith('#/')) return null
  let url
  try {
    url = new URL(raw, window.location.href)
  } catch {
    return null
  }
  if (url.origin !== window.location.origin) return null
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
  return url
}

function restoreAnchor(anchor) {
  if (!anchor?.dataset.pwaHref) return
  anchor.setAttribute('href', anchor.dataset.pwaHref)
  delete anchor.dataset.pwaHref
}

function armAnchor(anchor) {
  if (!anchor || anchor.dataset.pwaHref) return
  const url = readAppUrl(anchor)
  if (!url) return
  const next = pathOf(url)
  if (next === currentPath()) return
  anchor.dataset.pwaHref = anchor.getAttribute('href') || next
  // Same-document href: iOS will not hand the tap to the in-app browser.
  anchor.setAttribute('href', currentPath() || '/')
}

export function installInAppLinkGuard(router) {
  let armed = null
  let startX = 0
  let startY = 0

  const disarm = () => {
    restoreAnchor(armed)
    armed = null
  }

  // Only touch taps get the href swap. A mouse keeps its real href so that
  // cmd-click, middle-click and "copy link address" still target the route.
  document.addEventListener('pointerdown', (event) => {
    if (event.pointerType !== 'touch') return
    if (event.button !== 0 || hasModifier(event)) return
    const anchor = closestAnchor(event.target)
    if (!anchor) return
    armed = anchor
    startX = event.clientX
    startY = event.clientY
    armAnchor(anchor)
  }, { capture: true, passive: true })

  document.addEventListener('touchmove', (event) => {
    const touch = event.touches?.[0]
    if (!armed || !touch) return
    if (Math.abs(touch.clientX - startX) > 12 || Math.abs(touch.clientY - startY) > 12) {
      disarm()
    }
  }, { capture: true, passive: true })

  document.addEventListener('touchcancel', disarm, true)
  document.addEventListener('pointercancel', disarm, true)
  document.addEventListener('contextmenu', disarm, true)
  window.addEventListener('pagehide', disarm)

  document.addEventListener('click', (event) => {
    if (event.button !== 0 || hasModifier(event)) {
      disarm()
      return
    }
    const anchor = closestAnchor(event.target)
    if (!anchor) return
    const url = readAppUrl(anchor)
    if (!url) return
    event.preventDefault()
    const next = pathOf(url)
    restoreAnchor(anchor)
    armed = null
    if (next !== currentPath()) {
      router.push(next)
    }
  }, true)
}
