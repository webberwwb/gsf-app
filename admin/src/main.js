import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { checkAuth } from './utils/auth'

// Initialize app
const app = createApp(App)

// Register Service Worker - DISABLED in development mode
if ('serviceWorker' in navigator) {
  // Check if we're in development mode
  const isDevelopment = import.meta.env.DEV || 
                        window.location.hostname === 'localhost' || 
                        window.location.hostname === '127.0.0.1' ||
                        window.location.port === '3001'
  
  if (isDevelopment) {
    // Aggressively unregister service workers immediately
    // This must happen synchronously before any other code runs
    const unregisterServiceWorkers = async () => {
      try {
        // First, unregister all service workers
        const registrations = await navigator.serviceWorker.getRegistrations()
        await Promise.all(
          registrations.map(async (registration) => {
            try {
              // Unregister the service worker
              await registration.unregister()
              
              // Also try to update and skip waiting if there's a waiting worker
              if (registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' })
              }
              if (registration.installing) {
                registration.installing.postMessage({ type: 'SKIP_WAITING' })
              }
            } catch (err) {
              console.warn('Failed to unregister service worker:', err)
            }
          })
        )
        
        // Clear all caches
        if ('caches' in window) {
          const cacheNames = await caches.keys()
          await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
          )
        }
        
        // Force reload if there's still a controller (service worker controlling the page)
        if (navigator.serviceWorker.controller) {
          navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' })
          // Small delay to let the message be sent
          setTimeout(() => {
            window.location.reload()
          }, 100)
          return
        }
      } catch (error) {
        console.error('Error unregistering service workers:', error)
      }
    }
    
    // Run immediately
    unregisterServiceWorkers()
    
    // Also run on page load to catch any that might have registered after initial check
    window.addEventListener('load', unregisterServiceWorkers)
    
    // Prevent service worker from being registered in dev mode
    navigator.serviceWorker.register = function(...args) {
      return Promise.reject(new Error('Service worker registration disabled in development'))
    }
  } else {
    // Production mode - register service worker
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js', {
        updateViaCache: 'none', // Critical: don't cache the service worker file itself
        scope: '/'
      })
        .then((registration) => {
          // Check for updates every 2 minutes (more frequent for better UX)
          setInterval(() => {
            registration.update()
          }, 2 * 60 * 1000)
          
          // Also check for updates when page becomes visible
          document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
              registration.update()
            }
          })
          
          // Handle updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // Force reload to get the new version
                window.location.reload()
              }
            })
          })
        })
        .catch((error) => {
          console.error('Service Worker registration failed:', error)
        })
    })
  }
}

// Check authentication on app start
checkAuth()

app.use(router)
app.mount('#app')

