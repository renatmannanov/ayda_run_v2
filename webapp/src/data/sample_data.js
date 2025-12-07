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
    { id: 'cycling', icon: '🚴', label: 'Вело' }
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
