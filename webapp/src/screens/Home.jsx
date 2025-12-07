import React, { useState } from 'react'
import { BottomNav, CreateMenu, ActivityCard, Loading, ErrorMessage, EmptyState } from '../components'
import { useActivities, useJoinActivity } from '../hooks'
import { dayNames, isToday } from '../data/sample_data'

export default function Home() {
    const [mode, setMode] = useState('all') // 'my' | 'all'
    const [showPast, setShowPast] = useState(false)
    const [showCreateMenu, setShowCreateMenu] = useState(false)

    // Fetch activities
    const { data: activities = [], loading, error, refetch } = useActivities()

    // Join/Leave mutation
    const { mutate: joinActivity } = useJoinActivity()

    // Filter activities
    const getFilteredActivities = () => {
        if (!activities) return []
        const upcoming = activities.filter(a => !a.isPast)
        if (mode === 'my') {
            return upcoming.filter(a => a.isJoined)
        }
        return upcoming
    }

    const getPastActivities = () => {
        if (!activities) return []
        const past = activities.filter(a => a.isPast)
        if (mode === 'my') {
            return past.filter(a => a.isJoined)
        }
        return past
    }

    const filteredActivities = getFilteredActivities()
    const pastActivities = getPastActivities()

    // Group by day of week (Mon-Sun order)
    const groupByDay = (acts) => {
        const days = [1, 2, 3, 4, 5, 6, 0] // Mon to Sun
        const grouped = {}

        days.forEach(day => {
            // API returns day_of_week or calculate from date
            // Assuming backend parses date or we do it here.
            // For now, let's assume 'dayOfWeek' is available or date string can be parsed
            // sample_data had dayOfWeek property. Real API might send ISO string.
            // Let's rely on a helper if needed, but for now assuming data structure match or sample_data helper will be used on backend data
            // Actually, let's fix this safely:
            const dayMap = {}
            acts.forEach(a => {
                const d = new Date(a.date)
                const day = d.getDay() // 0-6 (Sun-Sat)
                if (!dayMap[day]) dayMap[day] = []
                dayMap[day].push(a)
            })
            grouped[day] = dayMap[day] || []
        })

        // Remap to Mon-Sun array if needed, but object keys are enough
        return grouped
    }

    const groupedActivities = groupByDay(filteredActivities)

    // Toggle join
    const handleJoinToggle = async (activityId) => {
        try {
            // Optimistic update could go here, but for now simple refetch
            await joinActivity(activityId)
            refetch()
        } catch (e) {
            console.error('Failed to toggle join', e)
        }
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
    const DaySection = ({ dayOfWeek, activities }) => {
        const today = isToday(dayOfWeek)
        const hasActivities = activities && activities.length > 0

        // Skip empty days for 'all' mode to reduce clutter? Or keep to show schedule slots? 
        // Protocol said: "filter by day...". 
        // If no activities, we can skip rendering the day header to clean up UI, 
        // unless it's Today.
        if (!hasActivities && !today) return null

        return (
            <div className="mb-4">
                <div className="flex items-center gap-2 mb-3">
                    <span className={`text-sm font-medium ${today ? 'text-gray-800' : 'text-gray-500'}`}>
                        {today ? `Сегодня, ${dayNames[dayOfWeek].toLowerCase()}` : dayNames[dayOfWeek]}
                    </span>
                    <div className="flex-1 border-b border-gray-200" />
                </div>

                {hasActivities ? (
                    activities.map(activity => (
                        <ActivityCard
                            key={activity.id}
                            activity={activity}
                            onJoinToggle={handleJoinToggle}
                        />
                    ))
                ) : (
                    <p className="text-sm text-gray-300 mb-3 pl-1">нет тренировок</p>
                )}
            </div>
        )
    }

    const upcomingCount = filteredActivities.length
    const hasUpcoming = upcomingCount > 0

    if (loading) return <div className="min-h-screen bg-gray-50 pt-12"><Loading text="Загружаем тренировки..." /></div>
    if (error) return <div className="min-h-screen bg-gray-50 pt-12"><ErrorMessage message={error} onRetry={refetch} /></div>

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <Toggle />
                <span className="text-sm text-gray-400">{upcomingCount}</span>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto px-4 py-4">
                {hasUpcoming ? (
                    <>
                        {/* Week days: Sort order - Today -> +6 days */}
                        {/* Simplification: Just iterating 1 (Mon) to 0 (Sun) might be confusing if today is Wed. 
                Ideally, show Today first. 
                Let's stick to Mon-Sun for consistency with calendar or strictly sorted by date.
                Current groupByDay is simple Mon-Sun.
            */}
                        {[1, 2, 3, 4, 5, 6, 0].map(day => (
                            <DaySection
                                key={day}
                                dayOfWeek={day}
                                activities={groupedActivities[day]}
                            />
                        ))}

                        {/* Past activities */}
                        {pastActivities.length > 0 && (
                            <div className="mt-6">
                                <button
                                    onClick={() => setShowPast(!showPast)}
                                    className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors mb-3"
                                >
                                    <span>Прошедшие ({pastActivities.length})</span>
                                    <span className={`transition-transform ${showPast ? 'rotate-180' : ''}`}>
                                        ▾
                                    </span>
                                </button>

                                {showPast && (
                                    <div className="space-y-3">
                                        {pastActivities.map(activity => (
                                            <ActivityCard
                                                key={activity.id}
                                                activity={activity}
                                                onJoinToggle={handleJoinToggle}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </>
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
