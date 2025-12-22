/**
 * Authentication utilities
 */

import apiClient from '../api/client'

/**
 * Check if user is authenticated
 * @returns {Promise<boolean>}
 */
export async function checkAuth() {
  const token = localStorage.getItem('auth_token')
  if (!token) {
    return false
  }

  try {
    const response = await apiClient.get('/auth/me')
    if (response.data.user) {
      localStorage.setItem('user', JSON.stringify(response.data.user))
      // Update token expiration time if provided (token was refreshed)
      if (response.data.token && response.data.token.expires_at) {
        localStorage.setItem('auth_token_expires_at', response.data.token.expires_at)
      }
      return true
    }
    return false
  } catch (error) {
    // Token invalid, clear it
    clearAuth()
    return false
  }
}

/**
 * Get current user from localStorage
 * @returns {Object|null}
 */
export function getCurrentUser() {
  const userStr = localStorage.getItem('user')
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
  return localStorage.getItem('auth_token')
}

/**
 * Check if token is expired (based on stored expiration time)
 * @returns {boolean}
 */
export function isTokenExpired() {
  const expiresAt = localStorage.getItem('auth_token_expires_at')
  if (!expiresAt) {
    return false // Assume valid if no expiration stored
  }
  return new Date(expiresAt) < new Date()
}

/**
 * Clear authentication data
 */
export function clearAuth() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user')
  localStorage.removeItem('auth_token_expires_at')
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

