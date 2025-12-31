/**
 * Authentication utilities
 * These are thin wrappers around the auth store for backward compatibility
 */

import { useAuthStore } from '../stores/auth'

/**
 * Check if user is authenticated
 * @returns {Promise<boolean>}
 */
export async function checkAuth() {
  const authStore = useAuthStore()
  return await authStore.checkAuth()
}

/**
 * Get current user from store
 * @returns {Object|null}
 */
export function getCurrentUser() {
  const authStore = useAuthStore()
  return authStore.currentUser
}

/**
 * Get auth token from store
 * @returns {string|null}
 */
export function getAuthToken() {
  const authStore = useAuthStore()
  return authStore.token
}

/**
 * Check if token is expired (based on stored expiration time)
 * @returns {boolean}
 */
export function isTokenExpired() {
  const authStore = useAuthStore()
  return authStore.isTokenExpired
}

/**
 * Clear authentication data
 */
export function clearAuth() {
  const authStore = useAuthStore()
  authStore.clearAuth()
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

