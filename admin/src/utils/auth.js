/**
 * Authentication utilities for Admin
 */

import apiClient from '../api/client'

/**
 * Check if admin is authenticated
 * Only clears auth on 401 errors - network errors won't log users out
 * @returns {Promise<boolean>}
 */
export async function checkAuth() {
  const token = localStorage.getItem('admin_auth_token')
  if (!token) {
    return false
  }

  try {
    const response = await apiClient.get('/auth/me')
    if (response.data.user) {
      localStorage.setItem('admin_user', JSON.stringify(response.data.user))
      return true
    }
    return false
  } catch (error) {
    // Only clear auth on 401 (unauthorized) - token is actually invalid
    // Network errors, timeouts, etc. shouldn't log users out
    if (error.response && error.response.status === 401) {
      clearAuth()
      return false
    }
    
    // For other errors, assume token is still valid (might be network issue)
    // Return true to allow access with cached token
    console.warn('Auth check failed (non-401 error), keeping cached token:', error.message)
    return true
  }
}

/**
 * Get current admin user from localStorage
 * @returns {Object|null}
 */
export function getCurrentUser() {
  const userStr = localStorage.getItem('admin_user')
  if (!userStr) {
    return null
  }
  try {
    return JSON.parse(userStr)
  } catch (error) {
    return null
  }
}

/**
 * Get auth token from localStorage
 * @returns {string|null}
 */
export function getAuthToken() {
  return localStorage.getItem('admin_auth_token')
}

/**
 * Clear authentication data
 */
export function clearAuth() {
  localStorage.removeItem('admin_auth_token')
  localStorage.removeItem('admin_user')
  localStorage.removeItem('admin_auth_token_expires_at')
}

/**
 * Require authentication - redirects to login if not authenticated
 * @returns {Promise<boolean>}
 */
export async function requireAuth() {
  const isAuthenticated = await checkAuth()
  if (!isAuthenticated) {
    window.location.href = '/login'
    return false
  }
  return true
}

