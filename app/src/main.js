import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { checkAuth } from './utils/auth'

// Initialize app
const app = createApp(App)

// Check authentication on app start
checkAuth().then((isAuthenticated) => {
  if (isAuthenticated) {
    console.log('✅ User authenticated from cached token')
  } else {
    console.log('ℹ️  No valid cached token, user needs to login')
  }
}).catch((error) => {
  console.error('❌ Error checking auth:', error)
})

app.use(router)

// Add error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('❌ Vue Error:', err)
  console.error('❌ Error Info:', info)
  console.error('❌ Component:', instance)
}

try {
  app.mount('#app')
  console.log('✅ App mounted successfully')
} catch (error) {
  console.error('❌ Failed to mount app:', error)
  document.getElementById('app').innerHTML = `
    <div style="padding: 20px; text-align: center;">
      <h2>应用加载失败</h2>
      <p>错误: ${error.message}</p>
      <button onclick="location.reload()">重新加载</button>
    </div>
  `
}

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
        updateViaCache: 'none' // Critical: don't cache the service worker file itself
      })
        .then((registration) => {
          console.log('✅ Service Worker registered:', registration)
          
          // Check for updates every 2 minutes (more frequent for better UX)
          setInterval(() => {
            registration.update().then(() => {
              console.log('🔄 Checked for Service Worker updates')
            })
          }, 2 * 60 * 1000)
          
          // Also check for updates when page becomes visible (important for iOS)
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
                // New service worker is installed but waiting to activate
                console.log('🔄 New version available!')
                // Show update notification to user
                showUpdateNotification(registration)
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

// Show update notification
function showUpdateNotification(registration) {
  // Create a simple update banner
  const banner = document.createElement('div')
  banner.id = 'update-banner'
  banner.innerHTML = `
    <div style="
      position: fixed;
      bottom: 70px;
      left: 0;
      right: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 16px;
      text-align: center;
      box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
      z-index: 9999;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
    ">
      <span>🔄 新版本可用</span>
      <button onclick="window.updateApp()" style="
        background: white;
        color: #667eea;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 600;
        cursor: pointer;
      ">立即更新</button>
      <button onclick="document.getElementById('update-banner').remove()" style="
        background: transparent;
        color: white;
        border: 1px solid white;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
      ">稍后</button>
    </div>
  `
  document.body.appendChild(banner)
  
  // Global update function
  window.updateApp = () => {
    if (registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
    window.location.reload()
  }
}

