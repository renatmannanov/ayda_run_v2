/**
 * Timezone utilities for consistent date handling.
 *
 * All dates sent to the server should include timezone information.
 * The server stores dates in UTC.
 */

/**
 * Get user's timezone string (IANA format).
 * Falls back to Europe/Moscow if detection fails.
 */
export function getUserTimezone() {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone
    } catch {
        return 'Europe/Moscow'
    }
}

/**
 * Get timezone offset string in format "+03:00" or "-05:00"
 */
export function getTimezoneOffset(date = new Date()) {
    const offset = -date.getTimezoneOffset()
    const sign = offset >= 0 ? '+' : '-'
    const hours = Math.floor(Math.abs(offset) / 60).toString().padStart(2, '0')
    const minutes = (Math.abs(offset) % 60).toString().padStart(2, '0')
    return `${sign}${hours}:${minutes}`
}

/**
 * Format a date and time for API submission with timezone.
 *
 * @param {string} date - Date in YYYY-MM-DD format
 * @param {string} time - Time in HH:MM format
 * @returns {string} ISO datetime with timezone, e.g., "2025-01-15T07:00:00+03:00"
 */
export function formatDateTimeForAPI(date, time) {
    const offset = getTimezoneOffset(new Date(`${date}T${time}`))
    return `${date}T${time}:00${offset}`
}

/**
 * Parse a date from API response for display.
 * API returns UTC dates, this converts to local time.
 *
 * @param {string} isoString - ISO datetime string from API
 * @returns {Date} Local Date object
 */
export function parseAPIDate(isoString) {
    return new Date(isoString)
}

/**
 * Get date part (YYYY-MM-DD) from Date object in local timezone.
 */
export function getLocalDateString(date) {
    const d = new Date(date)
    const year = d.getFullYear()
    const month = (d.getMonth() + 1).toString().padStart(2, '0')
    const day = d.getDate().toString().padStart(2, '0')
    return `${year}-${month}-${day}`
}

/**
 * Get time part (HH:MM) from Date object in local timezone.
 */
export function getLocalTimeString(date) {
    const d = new Date(date)
    const hours = d.getHours().toString().padStart(2, '0')
    const minutes = d.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
}
