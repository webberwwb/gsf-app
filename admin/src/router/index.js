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

// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('admin_auth_token')

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
        localStorage.setItem('admin_user', JSON.stringify(response.data.user))
      }

      // If on login page with valid token, redirect to dashboard
      if (to.path === '/login') {
        next('/')
        return
      }

      // Token is valid, allow navigation
      next()
      return
    } catch (error) {
      // Only clear token and redirect if it's a 401 (unauthorized)
      if (error.response && error.response.status === 401) {
        // Token invalid, clear it
        localStorage.removeItem('admin_auth_token')
        localStorage.removeItem('admin_user')
        localStorage.removeItem('admin_auth_token_expires_at')

        // Redirect to login if route requires auth
        if (to.meta.requiresAuth) {
          next('/login')
          return
        }
      } else {
        // Network error or other issue - token might still be valid
        console.warn('Token validation failed (non-401 error), allowing access with cached token:', error.message)

        // If on login page with token (even if can't validate), redirect to dashboard
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

