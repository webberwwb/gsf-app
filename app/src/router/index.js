import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top when navigating to a new route
    // This ensures content is not cut off on mobile devices
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0, behavior: 'instant' }
    }
  },
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/Home.vue'),
      meta: { requiresAuth: false, showBottomNav: true }
    },
    {
      path: '/favorites',
      name: 'Favorites',
      component: () => import('../views/Favorites.vue'),
      meta: { requiresAuth: true, showBottomNav: true }
    },
    {
      path: '/cart',
      name: 'Cart',
      component: () => import('../views/Cart.vue'),
      meta: { requiresAuth: false, showBottomNav: true }
    },
    {
      path: '/me',
      name: 'Me',
      component: () => import('../views/Me.vue'),
      meta: { requiresAuth: false, showBottomNav: true }
    },
    {
      path: '/group-deals',
      name: 'GroupDeals',
      component: () => import('../views/GroupDeals.vue'),
      meta: { requiresAuth: false, showBottomNav: true }
    },
    {
      path: '/group-deals/:id',
      name: 'GroupDealDetail',
      component: () => import('../views/GroupDealDetail.vue'),
      meta: { requiresAuth: false, showBottomNav: true }
    },
    {
      path: '/checkout',
      name: 'Checkout',
      component: () => import('../views/Checkout.vue'),
      meta: { requiresAuth: false, showBottomNav: false } // Will check auth in component
    },
    {
      path: '/order-result',
      name: 'OrderResult',
      component: () => import('../views/OrderResult.vue'),
      meta: { requiresAuth: true, showBottomNav: false }
    },
    {
      path: '/orders',
      name: 'Orders',
      component: () => import('../views/Orders.vue'),
      meta: { requiresAuth: false, showBottomNav: true } // Will show "未登录" message if not authenticated
    },
    {
      path: '/orders/:id',
      name: 'OrderDetail',
      component: () => import('../views/OrderDetail.vue'),
      meta: { requiresAuth: true, showBottomNav: true }
    },
    {
      path: '/points-mall',
      name: 'PointsMall',
      component: () => import('../views/PointsMall.vue'),
      meta: { requiresAuth: true, showBottomNav: false }
    },
    {
      path: '/addresses',
      name: 'Addresses',
      component: () => import('../views/Addresses.vue'),
      meta: { requiresAuth: true, showBottomNav: false }
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresAuth: false, showBottomNav: false }
    }
  ]
})

// Track if we've validated auth on app startup
let authValidatedOnStartup = false

// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // Load auth from storage if not already loaded
  if (!authStore.token) {
    authStore.loadFromStorage()
  }
  
  // Only redirect to login for routes that explicitly require auth
  // Guest browsing is allowed for most routes
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
    return
  }
  
  // If token exists, check if we need to validate it
  if (authStore.token) {
    // Only validate token on app startup (first navigation)
    // This prevents constant API calls on every navigation
    if (!authValidatedOnStartup) {
      authValidatedOnStartup = true
      
      // Validate token - but don't block navigation on network errors
      try {
        const isValid = await authStore.checkAuth()
        // If token is invalid (401), checkAuth already cleared it
        if (!isValid && to.meta.requiresAuth) {
          next('/login')
          return
        }
      } catch (error) {
        // checkAuth handles errors internally and only clears on 401
        // For other errors, it returns true, so we allow navigation
        // If it was a 401, checkAuth cleared the token, so check again
        if (!authStore.token && to.meta.requiresAuth) {
          next('/login')
          return
        }
      }
    }
    
    // If on login page with token, redirect to home
    if (to.path === '/login') {
      next('/')
      return
    }
    
    // Token exists, allow navigation
    next()
    return
  }
  
  // No token, continue navigation (will be handled by requiresAuth check above)
  next()
})

// Ensure scroll to top after navigation completes (especially important for mobile)
router.afterEach((to, from) => {
  // Use nextTick to ensure DOM is updated before scrolling
  setTimeout(() => {
    window.scrollTo(0, 0)
    // Also try scrolling the document element for better mobile compatibility
    if (document.documentElement) {
      document.documentElement.scrollTop = 0
    }
    if (document.body) {
      document.body.scrollTop = 0
    }
  }, 0)
})

export default router
