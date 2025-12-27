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
                        window.location.hostname === '127.0.0.1'
  
  if (isDevelopment) {
    console.log('🚫 Service Worker disabled in development mode')
    // Unregister any existing service workers in development
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      for (const registration of registrations) {
        registration.unregister().then(() => {
          console.log('🗑️  Unregistered existing service worker')
        })
      }
    })
  } else {
    // Production mode - register service worker
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js', {
        updateViaCache: 'none', // Critical: don't cache the service worker file itself
        scope: '/'
      })
        .then((registration) => {
          console.log('✅ Admin Service Worker registered:', registration.scope)
          
          // Check for updates every 2 minutes (more frequent for better UX)
          setInterval(() => {
            registration.update().then(() => {
              console.log('🔄 Checked for Service Worker updates')
            })
          }, 2 * 60 * 1000)
          
          // Also check for updates when page becomes visible
          document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
              registration.update().then(() => {
                console.log('🔄 Checked for updates (page visible)')
              })
            }
          })
          
          // Handle updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing
            console.log('🆕 New Service Worker found')
            
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                console.log('🔄 New version available!')
                // Force reload to get the new version
                window.location.reload()
              }
            })
          })
        })
        .catch((error) => {
          console.error('❌ Service Worker registration failed:', error)
        })
    })
  }
}

// Check authentication on app start
checkAuth().then((isAuthenticated) => {
  if (isAuthenticated) {
    console.log('✅ Admin authenticated from cached token')
  } else {
    console.log('ℹ️  No valid cached token, admin needs to login')
  }
})

app.use(router)
app.mount('#app')

