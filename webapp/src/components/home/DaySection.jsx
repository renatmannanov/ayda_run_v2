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
                        onClick={() => onToggleExpansion(weekNumber, dayOfWeek)}
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
                                            onJoinToggle={onJoinToggle}
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
                                        onJoinToggle={onJoinToggle}
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
