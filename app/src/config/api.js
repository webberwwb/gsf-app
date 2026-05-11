/** Backend HTTP port in local dev (see backend/app.py PORT default). */
const DEV_BACKEND_PORT = '5015'

/**
 * API base URL for axios.
 * Dev default hits Flask directly on :5015 (avoids relying on Vite :3000 proxy).
 * Override with VITE_API_BASE_URL; production uses Dockerfile / cloudbuild.
 */
export function getApiBaseURL() {
  const fromEnv = import.meta.env.VITE_API_BASE_URL
  if (fromEnv) return fromEnv
  if (import.meta.env.DEV) {
    return `http://localhost:${DEV_BACKEND_PORT}/api`
  }
  return 'https://backend.grainstoryfarm.ca/api'
}

/**
 * Public URL of the consumer PWA (no trailing slash). Used for invite/share links.
 * - Set VITE_APP_PUBLIC_URL in build (e.g. https://app.grainstoryfarm.ca).
 * - Local dev: uses current browser origin (e.g. http://localhost:3000 or LAN).
 * - Production build without env: https://app.grainstoryfarm.ca
 */
export function getAppPublicOrigin() {
  const fromEnv = import.meta.env.VITE_APP_PUBLIC_URL
  if (fromEnv) return String(fromEnv).replace(/\/$/, '')
  if (import.meta.env.DEV && typeof window !== 'undefined') {
    return window.location.origin
  }
  if (import.meta.env.DEV) {
    return 'http://localhost:3000'
  }
  return 'https://app.grainstoryfarm.ca'
}

/**
 * Flask origin for routes outside /api (e.g. GET /invite/<code>).
 */
export function getBackendOrigin() {
  const fromEnv = import.meta.env.VITE_BACKEND_ORIGIN
  if (fromEnv) return String(fromEnv).replace(/\/$/, '')
  const base = getApiBaseURL()
  if (base.startsWith('http')) {
    return base.replace(/\/api\/?$/, '') || base
  }
  if (import.meta.env.DEV) {
    return `http://localhost:${DEV_BACKEND_PORT}`
  }
  return 'https://backend.grainstoryfarm.ca'
}
