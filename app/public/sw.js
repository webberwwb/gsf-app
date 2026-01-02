// Service Worker for PWA with Version Management and iOS-specific fixes
// UPDATE THIS VERSION NUMBER WHEN DEPLOYING NEW CHANGES
// This version is automatically updated by update-version.sh script
const VERSION = '2026.01.01.2317'
const CACHE_NAME = `gsf-app-v${VERSION}`
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/logos/gsf-icon.png'
]

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache).catch((err) => {
          console.error('Cache addAll failed:', err)
        })
      })
  )
  // Force the waiting service worker to become the active service worker
  self.skipWaiting()
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName)
          }
        })
      )
    })
  )
  // Take control of all pages immediately
  return self.clients.claim()
})

// Fetch event - Network First strategy with proper cache invalidation
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return
  }

  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return
  }

  const url = new URL(event.request.url)
  
  // CRITICAL: Always use Network First for HTML files
  // This ensures we always get the latest index.html with correct asset references
  if (url.pathname === '/' || url.pathname === '/index.html' || 
      event.request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(event.request, {
        cache: 'no-store', // Don't use HTTP cache
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      })
        .then((response) => {
          // Only cache if we got a valid response
          if (response && response.status === 200) {
            const responseToCache = response.clone()
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache)
            })
          }
          return response
        })
        .catch(() => {
          // Only fallback to cache if completely offline
          return caches.match(event.request)
        })
    )
    return
  }
  
  // Network First for API calls
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          return response
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(event.request)
        })
    )
    return
  }
  
  // Network First for hashed assets (JS, CSS with hash in filename)
  // Vite generates hashed filenames like index-ABC123.js
  // If the file has a hash, always check network first to ensure we get the latest
  const hasHashInFilename = /-[a-zA-Z0-9]{8,}\.(js|css)$/.test(url.pathname)
  
  if (hasHashInFilename) {
    event.respondWith(
      fetch(event.request, { cache: 'no-cache' })
        .then((response) => {
          if (response && response.status === 200) {
            // Cache the new version
            const responseToCache = response.clone()
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache)
            })
          }
          return response
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(event.request)
        })
    )
    return
  }
  
  // Cache First for static assets without hashes (images, icons, etc.)
  // These don't change often and can be cached
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response
        }
        return fetch(event.request).then((response) => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response
          }
          const responseToCache = response.clone()
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache)
          })
          return response
        })
      })
  )
})

// Listen for messages from the app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: VERSION })
  }
  
  // iOS-specific: Force update check
  if (event.data && event.data.type === 'CHECK_UPDATE') {
    self.registration.update()
  }
})

