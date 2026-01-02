import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('../views/Home.vue'),
      meta: { requiresAuth: true, showBottomNav: true }
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
      meta: { requiresAuth: true, showBottomNav: true }
    },
    {
      path: '/me',
      name: 'Me',
      component: () => import('../views/Me.vue'),
      meta: { requiresAuth: true, showBottomNav: true }
    },
    {
      path: '/group-deals',
      name: 'GroupDeals',
      component: () => import('../views/GroupDeals.vue'),
      meta: { requiresAuth: true, showBottomNav: true }
    },
    {
      path: '/group-deals/:id',
      name: 'GroupDealDetail',
      component: () => import('../views/GroupDealDetail.vue'),
      meta: { requiresAuth: true, showBottomNav: true }
    },
    {
      path: '/checkout',
      name: 'Checkout',
      component: () => import('../views/Checkout.vue'),
      meta: { requiresAuth: true, showBottomNav: false }
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
  
  // If route requires auth and no token, redirect to login
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

export default router
