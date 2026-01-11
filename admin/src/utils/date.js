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
 * @param {string} dateString - ISO date string (naive datetime from backend, treated as EST)
 * @returns {string} Formatted datetime string
 */
export function formatDateTimeEST_CN(dateString) {
  if (!dateString) return ''
  
  // Backend sends naive datetimes (e.g., "2024-01-15T23:59:59") which are stored in EST
  // Parse the date components manually to avoid timezone conversion issues
  // Match format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS.ffffff
  const match = dateString.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$/)
  if (match) {
    const [, year, month, day, hour, minute, second] = match
    const yearNum = parseInt(year)
    const monthNum = parseInt(month) - 1 // JavaScript months are 0-indexed
    const dayNum = parseInt(day)
    const hourNum = parseInt(hour)
    const minuteNum = parseInt(minute)
    
    // Create date object using local time (EST) - parse components directly
    // This ensures the time is displayed exactly as stored, without timezone conversion
    const date = new Date(yearNum, monthNum, dayNum, hourNum, minuteNum, parseInt(second || 0))
    
    // Format the date components directly to avoid any timezone issues
    // Use padStart to ensure 2-digit formatting
    const formattedYear = yearNum.toString()
    const formattedMonth = String(monthNum + 1).padStart(2, '0')
    const formattedDay = String(dayNum).padStart(2, '0')
    const formattedHour = String(hourNum).padStart(2, '0')
    const formattedMinute = String(minuteNum).padStart(2, '0')
    
    // Return in format: YYYY-MM-DD HH:MM
    return `${formattedYear}-${formattedMonth}-${formattedDay} ${formattedHour}:${formattedMinute}`
  }
  
  // Fallback to normal parsing if format doesn't match
  const date = new Date(dateString)
  if (isNaN(date.getTime())) {
    return dateString // Return original string if parsing fails
  }
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
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

/**
 * Format pickup date/time - shows "时间待定" (TBD) for time if it's midnight (00:00:00)
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted pickup date string
 */
export function formatPickupDateTime_CN(dateString) {
  if (!dateString) return ''
  
  // Parse the date components manually to avoid timezone conversion issues
  const match = dateString.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$/)
  if (match) {
    const [, year, month, day, hour, minute] = match
    const hourNum = parseInt(hour)
    const minuteNum = parseInt(minute)
    
    // Check if time is midnight (00:00:00)
    if (hourNum === 0 && minuteNum === 0) {
      // Only show date, time is TBD
      return `${year}-${month}-${day} 时间待定`
    }
    
    // Show full datetime
    const formattedHour = String(hourNum).padStart(2, '0')
    const formattedMinute = String(minuteNum).padStart(2, '0')
    return `${year}-${month}-${day} ${formattedHour}:${formattedMinute}`
  }
  
  // Fallback to formatDateTimeEST_CN
  return formatDateTimeEST_CN(dateString)
}
