import { createRouter, createWebHistory } from 'vue-router'
import apiClient from '../api/client'

const router = createRouter({
  history: createWebHistory('/'),
  routes: [
    {
      path: '/',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('../views/DashboardContent.vue')
        },
        {
          path: 'products',
          name: 'Products',
          component: () => import('../views/Products.vue')
        },
        {
          path: 'group-deals',
          name: 'GroupDeals',
          component: () => import('../views/GroupDeals.vue')
        },
        {
          path: 'group-deals/:id',
          name: 'GroupDealDetail',
          component: () => import('../views/GroupDealDetail.vue')
        },
        {
          path: 'orders',
          name: 'Orders',
          component: () => import('../views/Orders.vue')
        },
        {
          path: 'users',
          name: 'Users',
          component: () => import('../views/Users.vue')
        },
        {
          path: 'suppliers',
          name: 'Suppliers',
          component: () => import('../views/Suppliers.vue')
        },
        {
          path: 'shipping-fee',
          name: 'ShippingFeeManagement',
          component: () => import('../views/ShippingFeeManagement.vue')
        }
      ]
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresAuth: false }
    }
  ]
})

// Track if we've validated auth on app startup
let authValidatedOnStartup = false

// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('admin_auth_token')

  // If route requires auth and no token, redirect to login
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  // If token exists, check if we need to validate it
  if (token) {
    // Only validate token on app startup (first navigation)
    // This prevents constant API calls on every navigation
    if (!authValidatedOnStartup) {
      authValidatedOnStartup = true
      
      // Validate token - but don't block navigation on network errors
      try {
        const response = await apiClient.get('/auth/me')
        // Token is valid, store user info
        if (response.data.user) {
          localStorage.setItem('admin_user', JSON.stringify(response.data.user))
        }
      } catch (error) {
        // Only clear token on 401 - network errors shouldn't log users out
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('admin_auth_token')
          localStorage.removeItem('admin_user')
          localStorage.removeItem('admin_auth_token_expires_at')
          
          // If we're on a protected route, redirect to login
          if (to.meta.requiresAuth) {
            next('/login')
            return
          }
        } else {
          // For other errors, keep the token and allow navigation
          console.warn('Token validation failed (non-401 error), keeping cached token:', error.message)
        }
      }
    }
    
    // If on login page with token, redirect to dashboard
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

