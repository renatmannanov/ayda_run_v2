import { getWeekStart, getWeekEnd, getWeekNumber } from '../data/sample_data'

/**
 * Group activities by week and day
 */
export function groupActivitiesByWeekAndDay(activities) {
    if (!activities) return []

    // Group by week number
    const weekMap = {}
    const today = new Date()

    activities.forEach(activity => {
        const activityDate = new Date(activity.date)
        const weekNum = getWeekNumber(activityDate, today)

        if (!weekMap[weekNum]) {
            weekMap[weekNum] = {
                weekNumber: weekNum,
                weekStart: getWeekStart(activityDate),
                weekEnd: getWeekEnd(activityDate),
                days: {}
            }
        }

        const dayOfWeek = activityDate.getDay()
        if (!weekMap[weekNum].days[dayOfWeek]) {
            weekMap[weekNum].days[dayOfWeek] = []
        }

        weekMap[weekNum].days[dayOfWeek].push(activity)
    })

    // Sort activities within each day by time
    Object.values(weekMap).forEach(week => {
        Object.values(week.days).forEach(dayActivities => {
            dayActivities.sort((a, b) => new Date(a.date) - new Date(b.date))
        })
    })

    // Convert to array and sort by week number
    const weeks = Object.values(weekMap).sort((a, b) => a.weekNumber - b.weekNumber)

    return weeks
}

/**
 * Format week range for display
 */
export function getWeekRangeText(week) {
    if (!week) return ''

    const start = week.weekStart
    const end = week.weekEnd

    const formatDay = (date) => {
        return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
    }

    return `${formatDay(start)} - ${formatDay(end)}`
}

/**
 * Get total activities count for a week
 */
export function getWeekActivityCount(week) {
    if (!week) return 0
    return Object.values(week.days).reduce((sum, dayActivities) => sum + dayActivities.length, 0)
}
