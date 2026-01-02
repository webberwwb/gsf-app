import { defineStore } from 'pinia'
import apiClient from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    tokenExpiresAt: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
    isTokenExpired: (state) => {
      if (!state.tokenExpiresAt) return false
      return new Date(state.tokenExpiresAt) < new Date()
    },
    hasWechat: (state) => {
      return !!(state.user && state.user.wechat && state.user.wechat.trim().length > 0)
    }
  },
  
  actions: {
    /**
     * Set authentication data
     */
    setAuth(token, user, expiresAt = null) {
      this.token = token
      this.user = user
      this.tokenExpiresAt = expiresAt
      
      // Persist to localStorage for page refreshes
      if (token) {
        localStorage.setItem('auth_token', token)
      }
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      }
      if (expiresAt) {
        localStorage.setItem('auth_token_expires_at', expiresAt)
      }
    },
    
    /**
     * Update user data
     */
    setUser(user) {
      this.user = user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      }
    },
    
    /**
     * Load auth data from localStorage (for page refresh)
     */
    loadFromStorage() {
      const token = localStorage.getItem('auth_token')
      const userStr = localStorage.getItem('user')
      const expiresAt = localStorage.getItem('auth_token_expires_at')
      
      if (token) {
        this.token = token
      }
      
      if (userStr) {
        try {
          this.user = JSON.parse(userStr)
        } catch (error) {
          console.error('Failed to parse user from storage:', error)
        }
      }
      
      if (expiresAt) {
        this.tokenExpiresAt = expiresAt
      }
    },
    
    /**
     * Clear authentication data
     */
    clearAuth() {
      this.token = null
      this.user = null
      this.tokenExpiresAt = null
      
      // Clear from localStorage
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      localStorage.removeItem('auth_token_expires_at')
    },
    
    /**
     * Check authentication status with API
     * Only clears auth on 401 errors - network errors won't log users out
     */
    async checkAuth() {
      if (!this.token) {
        // Try to load from storage first
        this.loadFromStorage()
        if (!this.token) {
          return false
        }
      }
      
      try {
        const response = await apiClient.get('/auth/me')
        if (response.data.user) {
          this.setUser(response.data.user)
          
          // Update token expiration if provided (token was refreshed)
          if (response.data.token && response.data.token.expires_at) {
            this.tokenExpiresAt = response.data.token.expires_at
            localStorage.setItem('auth_token_expires_at', response.data.token.expires_at)
          }
          
          return true
        }
        return false
      } catch (error) {
        // Only clear auth on 401 (unauthorized) - token is actually invalid
        // Network errors, timeouts, etc. shouldn't log users out
        if (error.response && error.response.status === 401) {
          this.clearAuth()
          return false
        }
        
        // For other errors, assume token is still valid (might be network issue)
        // Return true to allow access with cached token
        console.warn('Auth check failed (non-401 error), keeping cached token:', error.message)
        return true
      }
    },
    
    /**
     * Login with phone and OTP
     */
    async login(phone, otp) {
      // Call the correct backend endpoint for OTP verification
      const response = await apiClient.post('/auth/phone/verify', {
        phone,
        otp
      })
      
      const { token, user, expires_at } = response.data
      this.setAuth(token, user, expires_at)
      
      return response.data
    },
    
    /**
     * Logout
     */
    logout() {
      this.clearAuth()
    },
    
    /**
     * Update user's WeChat ID
     */
    async updateWechat(wechat) {
      try {
        const response = await apiClient.put('/auth/me/wechat', {
          wechat: wechat.trim()
        })
        
        if (response.data.user) {
          this.setUser(response.data.user)
          return true
        }
        return false
      } catch (error) {
        console.error('Failed to update wechat:', error)
        throw error
      }
    }
  }
})

