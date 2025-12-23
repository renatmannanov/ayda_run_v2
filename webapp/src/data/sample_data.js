/**
 * Constants & Helpers
 * Extracted from original sample data
 */

// ============================================================================
// Constants & Enums
// ============================================================================

export const sportTypes = [
    { id: 'running', icon: '🏃', label: 'Бег' },
    { id: 'trail', icon: '⛰️', label: 'Трейл' },
    { id: 'hiking', icon: '🥾', label: 'Хайкинг' },
    { id: 'cycling', icon: '🚴', label: 'Вело' },
    { id: 'yoga', icon: '🧘', label: 'Йога' },
    { id: 'workout', icon: '💪', label: 'Workout' },
]

export const difficultyLevels = [
    { id: 'easy', label: 'Легкая' },
    { id: 'medium', label: 'Средняя' },
    { id: 'hard', label: 'Сложная' }
]

export const dayNames = {
    0: 'Вс',
    1: 'Пн',
    2: 'Вт',
    3: 'Ср',
    4: 'Чт',
    5: 'Пт',
    6: 'Сб'
}

export const fullDayNames = {
    0: 'Воскресенье',
    1: 'Понедельник',
    2: 'Вторник',
    3: 'Среда',
    4: 'Четверг',
    5: 'Пятница',
    6: 'Суббота'
}

// ============================================================================
// Helpers
// ============================================================================

export const getSportIcon = (type) => {
    return sportTypes.find(s => s.id === type)?.icon || '🏃'
}

export const getSportLabel = (type) => {
    return sportTypes.find(s => s.id === type)?.label || type
}

export const getDifficultyLabel = (level) => {
    return difficultyLevels.find(d => d.id === level)?.label || level
}

export const formatTime = (date) => {
    if (!date) return ''
    const d = new Date(date)
    return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

export const formatDate = (date) => {
    if (!date) return ''
    const d = new Date(date)
    return d.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric', month: 'short' })
}

export const isToday = (dayOfWeek) => {
    return new Date().getDay() === dayOfWeek
}

export const pluralize = (count, one, few, many) => {
    const n = Math.abs(count) % 100
    const n1 = n % 10
    if (n > 10 && n < 20) return many
    if (n1 > 1 && n1 < 5) return few
    if (n1 === 1) return one
    return many
}

export const pluralizeMembers = (count = 0) => {
    return `${count} ${pluralize(count, 'участник', 'участника', 'участников')}`
}

export const pluralizeGroups = (count = 0) => {
    return `${count} ${pluralize(count, 'группа', 'группы', 'групп')}`
}

/**
 * Get the start of the week (Monday) for a given date
 */
export const getWeekStart = (date) => {
    const d = new Date(date)
    const day = d.getDay()
    const diff = day === 0 ? -6 : 1 - day // Adjust for Monday as first day
    const monday = new Date(d)
    monday.setDate(d.getDate() + diff)
    monday.setHours(0, 0, 0, 0)
    return monday
}

/**
 * Get the end of the week (Sunday) for a given date
 */
export const getWeekEnd = (date) => {
    const monday = getWeekStart(date)
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    sunday.setHours(23, 59, 59, 999)
    return sunday
}

/**
 * Get week bounds (Monday to Sunday) for a given date
 */
export const getWeekBounds = (date) => {
    return {
        start: getWeekStart(date),
        end: getWeekEnd(date)
    }
}

/**
 * Get the week number relative to a reference date
 * Week 0 is the current week, 1 is next week, -1 is last week, etc.
 */
export const getWeekNumber = (date, referenceDate = new Date()) => {
    const weekStart = getWeekStart(date)
    const refWeekStart = getWeekStart(referenceDate)
    const diffTime = weekStart.getTime() - refWeekStart.getTime()
    const diffWeeks = Math.floor(diffTime / (7 * 24 * 60 * 60 * 1000))
    return diffWeeks
}

/**
 * Check if a date is in the past (before today)
 */
export const isPastDate = (date) => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const checkDate = new Date(date)
    checkDate.setHours(0, 0, 0, 0)
    return checkDate < today
}
