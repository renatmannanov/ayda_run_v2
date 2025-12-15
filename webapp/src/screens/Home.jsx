import React, { useState, useEffect, useRef, useCallback } from 'react'
import { BottomNav, CreateMenu, ActivityCard, Loading, ErrorMessage, EmptyState } from '../components'
import { useActivities, useJoinActivity } from '../hooks'
import { dayNames, isToday, getWeekStart, getWeekEnd, getWeekNumber, isPastDate } from '../data/sample_data'

export default function Home() {
    const [mode, setMode] = useState('all') // 'my' | 'all'
    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [currentWeekIndex, setCurrentWeekIndex] = useState(null) // Index of currently displayed week
    const [expandedDays, setExpandedDays] = useState({}) // Track which past days are expanded

    // Fetch activities
    const { data: activities = [], loading, error, refetch } = useActivities()

    // Join/Leave mutation
    const { mutate: joinActivity } = useJoinActivity()

    // Group activities by week and day
    const groupActivitiesByWeekAndDay = useCallback(() => {
        if (!activities) return []

        // Filter based on mode
        let filtered = activities
        if (mode === 'my') {
            filtered = activities.filter(a => a.isJoined)
        }

        // Group by week number
        const weekMap = {}
        const today = new Date()

        filtered.forEach(activity => {
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
    }, [activities, mode])

    const allWeeks = groupActivitiesByWeekAndDay()

    // Set initial week to current week (weekNumber === 0) on first load
    useEffect(() => {
        if (currentWeekIndex === null && allWeeks.length > 0) {
            const currentWeekIdx = allWeeks.findIndex(w => w.weekNumber === 0)
            setCurrentWeekIndex(currentWeekIdx >= 0 ? currentWeekIdx : 0)
        }
    }, [allWeeks, currentWeekIndex])

    // Get currently displayed week
    const displayedWeek = currentWeekIndex !== null && allWeeks[currentWeekIndex]
        ? allWeeks[currentWeekIndex]
        : null

    // Navigation handlers
    const goToPreviousWeek = () => {
        if (currentWeekIndex > 0) {
            setCurrentWeekIndex(currentWeekIndex - 1)
        }
    }

    const goToNextWeek = () => {
        if (currentWeekIndex < allWeeks.length - 1) {
            setCurrentWeekIndex(currentWeekIndex + 1)
        }
    }

    const canGoPrevious = currentWeekIndex > 0
    const canGoNext = currentWeekIndex < allWeeks.length - 1

    // Toggle join
    const handleJoinToggle = async (activityId) => {
        try {
            await joinActivity(activityId)
            refetch()
        } catch (e) {
            console.error('Failed to toggle join', e)
        }
    }

    // Toggle day expansion
    const toggleDayExpansion = (weekNum, dayOfWeek) => {
        const key = `${weekNum}-${dayOfWeek}`
        setExpandedDays(prev => ({
            ...prev,
            [key]: !prev[key]
        }))
    }

    // Toggle component
    const Toggle = () => (
        <div className="flex items-center gap-1 text-sm">
            <button
                onClick={() => setMode('my')}
                className={`transition-colors ${mode === 'my'
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
            >
                Мои
            </button>
            <span className="text-gray-300">/</span>
            <button
                onClick={() => setMode('all')}
                className={`transition-colors ${mode === 'all'
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-400 hover:text-gray-600'
                    }`}
            >
                Все
            </button>
        </div>
    )

    // Day Section component
    const DaySection = ({ weekNumber, dayOfWeek, activities }) => {
        const hasActivities = activities && activities.length > 0

        const now = new Date()

        // Check if this is today
        const isTodayDay = isToday(dayOfWeek)

        // For current week (weekNumber === 0), check if the day has passed
        // For past weeks (weekNumber < 0), ALL days should be collapsed
        const isCurrentWeek = weekNumber === 0
        const isPastWeek = weekNumber < 0
        const currentDayOfWeek = now.getDay()

        // Convert to Mon-Sun order for comparison (Mon=1, Tue=2, ..., Sun=7)
        const dayOrder = dayOfWeek === 0 ? 7 : dayOfWeek
        const currentDayOrder = currentDayOfWeek === 0 ? 7 : currentDayOfWeek

        // A day should be collapsed if:
        // 1. It's in a past week (weekNumber < 0) - ALL days collapsed
        // 2. OR it's in the current week (weekNumber === 0) AND the day of week is before current day
        const isPastDay = isPastWeek || (isCurrentWeek && dayOrder < currentDayOrder)

        // Check which activities are actually past (time has passed)
        const pastActivities = hasActivities ? activities.filter(a => new Date(a.date) < now) : []
        const futureActivities = hasActivities ? activities.filter(a => new Date(a.date) >= now) : []
        const allPast = hasActivities && pastActivities.length === activities.length

        const expandKey = `${weekNumber}-${dayOfWeek}`
        const isExpanded = expandedDays[expandKey] || false

        // Count activities for this day
        const activityCount = hasActivities ? activities.length : 0

        return (
            <div className="mb-4">
                {/* Day Header */}
                <div className="flex items-center gap-2 mb-3">
                    {isPastDay ? (
                        <button
                            onClick={() => toggleDayExpansion(weekNumber, dayOfWeek)}
                            className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-600 transition-colors"
                        >
                            <span>{dayNames[dayOfWeek]}</span>
                            <span className={`text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                                ▾
                            </span>
                        </button>
                    ) : (
                        <span className={`text-sm font-medium ${isTodayDay ? 'text-gray-800' : 'text-gray-500'}`}>
                            {isTodayDay ? `Сегодня, ${dayNames[dayOfWeek].toLowerCase()}` : dayNames[dayOfWeek]}
                        </span>
                    )}
                    <div className="flex-1 border-b border-gray-200" />
                    <span className="text-xs text-gray-400">{activityCount}</span>
                </div>

                {/* Activities */}
                {isPastDay ? (
                    isExpanded && (
                        hasActivities ? (
                            <div className="space-y-3">
                                {activities.map(activity => {
                                    const isPast = new Date(activity.date) < now
                                    return (
                                        <div key={activity.id} className={isPast ? 'opacity-50' : ''}>
                                            <ActivityCard
                                                activity={activity}
                                                onJoinToggle={handleJoinToggle}
                                            />
                                        </div>
                                    )
                                })}
                            </div>
                        ) : (
                            <p className="text-sm text-gray-300 mb-3 pl-1">В этот день нет активностей</p>
                        )
                    )
                ) : (
                    hasActivities ? (
                        <div className="space-y-3">
                            {activities.map(activity => {
                                const isPast = new Date(activity.date) < now
                                return (
                                    <div key={activity.id} className={isPast ? 'opacity-50' : ''}>
                                        <ActivityCard
                                            activity={activity}
                                            onJoinToggle={handleJoinToggle}
                                        />
                                    </div>
                                )
                            })}
                        </div>
                    ) : (
                        <p className="text-sm text-gray-300 mb-3 pl-1">В этот день нет активностей</p>
                    )
                )}
            </div>
        )
    }

    // Calculate total activities count for the current week only
    const totalCount = displayedWeek
        ? Object.values(displayedWeek.days).reduce((sum, dayActivities) => sum + dayActivities.length, 0)
        : 0

    const hasActivities = totalCount > 0

    // Format week range for display
    const getWeekRangeText = (week) => {
        if (!week) return ''
        const start = week.weekStart
        const end = week.weekEnd

        const formatDay = (date) => {
            return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
        }

        return `${formatDay(start)} - ${formatDay(end)}`
    }

    if (loading) return <div className="min-h-screen bg-gray-50 pt-12"><Loading text="Загружаем тренировки..." /></div>
    if (error) return <div className="min-h-screen bg-gray-50 pt-12"><ErrorMessage message={error} onRetry={refetch} /></div>

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <Toggle />
                <span className="text-sm text-gray-400">{totalCount}</span>
            </div>

            {/* Week Navigation */}
            {displayedWeek && (
                <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-[52px] z-10">
                    <button
                        onClick={goToPreviousWeek}
                        disabled={!canGoPrevious}
                        className={`text-2xl ${canGoPrevious ? 'text-gray-700 hover:text-gray-900' : 'text-gray-300'}`}
                    >
                        ‹
                    </button>
                    <div className="text-center">
                        <div className="text-sm font-medium text-gray-900">
                            {displayedWeek.weekNumber === 0 ? 'Текущая неделя' :
                                displayedWeek.weekNumber > 0 ? `+${displayedWeek.weekNumber} неделя` :
                                    `${displayedWeek.weekNumber} неделя`}
                        </div>
                        <div className="text-xs text-gray-500">
                            {getWeekRangeText(displayedWeek)}
                        </div>
                    </div>
                    <button
                        onClick={goToNextWeek}
                        disabled={!canGoNext}
                        className={`text-2xl ${canGoNext ? 'text-gray-700 hover:text-gray-900' : 'text-gray-300'}`}
                    >
                        ›
                    </button>
                </div>
            )}

            {/* Content */}
            <div className="flex-1 overflow-auto px-4 py-4">
                {hasActivities && displayedWeek ? (
                    <div className="mb-6">
                        {/* Render days in Mon-Sun order */}
                        {[1, 2, 3, 4, 5, 6, 0].map(dayOfWeek => (
                            <DaySection
                                key={`${displayedWeek.weekNumber}-${dayOfWeek}`}
                                weekNumber={displayedWeek.weekNumber}
                                dayOfWeek={dayOfWeek}
                                activities={displayedWeek.days[dayOfWeek]}
                            />
                        ))}
                    </div>
                ) : (
                    <EmptyState
                        icon="📅"
                        title="Пока пусто"
                        description="Нет предстоящих тренировок"
                        actionText={mode === 'my' ? "Смотреть все" : null}
                        onAction={() => setMode('all')}
                    />
                )}
            </div>

            {/* Bottom Navigation - Fixed */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto">
                <BottomNav onCreateClick={() => setShowCreateMenu(true)} />
            </div>

            {/* Create Menu */}
            <CreateMenu
                isOpen={showCreateMenu}
                onClose={() => setShowCreateMenu(false)}
            />
        </div>
    )
}
