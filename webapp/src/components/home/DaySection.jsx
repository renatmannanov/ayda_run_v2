import React from 'react'
import { ActivityCard } from '../index'
import { dayNames, isToday } from '../../data/sample_data'

export function DaySection({
    weekNumber,
    dayOfWeek,
    activities,
    expandedDays,
    onToggleExpansion,
    onJoinToggle
}) {
    const hasActivities = activities && activities.length > 0
    const now = new Date()

    // Check if this is today (only on current week)
    const isTodayDay = isToday(dayOfWeek, weekNumber)

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

    const expandKey = `${weekNumber}-${dayOfWeek}`
    const isExpanded = expandedDays[expandKey] || false

    // Count activities for this day
    const activityCount = hasActivities ? activities.length : 0

    // Get day display name
    const getDayName = () => {
        if (isTodayDay) return `Сегодня, ${dayNames[dayOfWeek].toLowerCase()}`
        return dayNames[dayOfWeek]
    }

    // Compact row for days without activities
    if (!hasActivities) {
        return (
            <div className="border-b border-gray-100">
                <button
                    onClick={() => isPastDay && onToggleExpansion(weekNumber, dayOfWeek)}
                    className="w-full flex items-center py-3 hover:bg-gray-50 transition-colors relative"
                    disabled={!isPastDay}
                >
                    {/* Day name - left */}
                    <span className={`text-sm flex-shrink-0 ${isTodayDay ? 'font-medium text-gray-800' : isPastDay ? 'text-gray-400' : 'font-medium text-gray-600'}`}>
                        {getDayName()}
                        {isPastDay && (
                            <span className={`ml-1 text-xs transition-transform inline-block ${isExpanded ? 'rotate-180' : ''}`}>
                                ▾
                            </span>
                        )}
                    </span>

                    {/* Left line */}
                    <div className="flex-1 border-b border-gray-200 mx-3" />

                    {/* "нет активностей" - absolutely centered */}
                    <span className="absolute left-1/2 -translate-x-1/2 text-xs text-gray-400 bg-gray-50 px-2">
                        нет активностей
                    </span>

                    {/* Right line */}
                    <div className="flex-1 border-b border-gray-200 mx-3" />

                    {/* Count - right */}
                    <span className="text-sm text-gray-400 flex-shrink-0">0</span>
                </button>
            </div>
        )
    }

    // Regular row for days with activities
    return (
        <div className="border-b border-gray-100">
            {/* Day Header */}
            <button
                onClick={() => isPastDay && onToggleExpansion(weekNumber, dayOfWeek)}
                className="w-full flex items-center py-3 hover:bg-gray-50 transition-colors"
                disabled={!isPastDay}
            >
                {/* Day name - left */}
                <span className={`text-sm flex-shrink-0 ${isTodayDay ? 'font-medium text-gray-800' : isPastDay ? 'text-gray-400' : 'font-medium text-gray-600'}`}>
                    {getDayName()}
                    {isPastDay && (
                        <span className={`ml-1 text-xs transition-transform inline-block ${isExpanded ? 'rotate-180' : ''}`}>
                            ▾
                        </span>
                    )}
                </span>

                {/* Line */}
                <div className="flex-1 border-b border-gray-200 mx-3" />

                {/* Count - right */}
                <span className="text-sm text-gray-800 font-medium flex-shrink-0">{activityCount}</span>
            </button>

            {/* Activities */}
            {(!isPastDay || isExpanded) && (
                <div className="pb-3 space-y-3">
                    {activities.map(activity => {
                        const isPast = new Date(activity.date) < now
                        return (
                            <div key={activity.id} className={isPast ? 'opacity-80' : ''}>
                                <ActivityCard
                                    activity={activity}
                                    onJoinToggle={onJoinToggle}
                                />
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
