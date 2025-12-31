/**
 * Date utility functions
 * All users are in EST timezone, so we can parse and format dates normally
 * Backend sends dates without timezone (e.g., "2024-01-15T00:00:00")
 * Browser will interpret them in user's local timezone (EST)
 */

/**
 * Format date in Chinese locale
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
export function formatDateEST_CN(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

/**
 * Format datetime in Chinese locale
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted datetime string
 */
export function formatDateTimeEST_CN(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Get current date/time
 * @returns {Date} Current date
 */
export function getNowEST() {
  return new Date()
}

/**
 * Parse date string (no conversion needed, browser handles it)
 * @param {string} dateString - ISO date string
 * @returns {Date} Date object
 */
export function parseDateEST(dateString) {
  if (!dateString) return null
  return new Date(dateString)
}
