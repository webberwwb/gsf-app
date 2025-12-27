import { createRouter, createWebHistory } from 'vue-router'
import apiClient from '../api/client'

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

// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('auth_token')
  
  // If route requires auth and no token, redirect to login
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  // If token exists, try to validate it
  if (token) {
    try {
      const response = await apiClient.get('/auth/me')
      // Token is valid, store user info
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user))
      }
      
      // If on login page with valid token, redirect to home
      if (to.path === '/login') {
        next('/')
        return
      }
      
      // Token is valid, allow navigation
      next()
      return
    } catch (error) {
      // Only clear token and redirect if it's a 401 (unauthorized)
      // Other errors (network, 500, etc.) might be temporary - allow access with cached token
      if (error.response && error.response.status === 401) {
        // Token invalid, clear it
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        localStorage.removeItem('auth_token_expires_at')
        
        // Redirect to login if route requires auth
        if (to.meta.requiresAuth) {
          next('/login')
          return
        }
      } else {
        // Network error or other issue - token might still be valid
        // Allow navigation but log the error
        console.warn('Token validation failed (non-401 error), allowing access with cached token:', error.message)
        
        // If on login page with token (even if can't validate), redirect to home
        if (to.path === '/login') {
          next('/')
          return
        }
      }
    }
  }
  
  // No token or validation passed, continue navigation
  next()
})

export default router
