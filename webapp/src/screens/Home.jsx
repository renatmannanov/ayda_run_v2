import React, { useState, useEffect, useMemo } from 'react'
import { BottomNav, CreateMenu, Loading, ErrorMessage, EmptyState } from '../components'
import { DaySection } from '../components/home/DaySection'
import { ModeToggle } from '../components/home/ModeToggle'
import { useActivities, useJoinActivity } from '../hooks'
import { groupActivitiesByWeekAndDay, getWeekRangeText, getWeekActivityCount } from '../utils/weekUtils'

export default function Home() {
    const [mode, setMode] = useState('all') // 'my' | 'all'
    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [currentWeekIndex, setCurrentWeekIndex] = useState(null)
    const [expandedDays, setExpandedDays] = useState({})

    // Fetch activities
    const { data: activities = [], isLoading: loading, error, refetch } = useActivities()

    // Join/Leave mutation
    const joinMutation = useJoinActivity()

    // Filter activities by mode
    const filteredActivities = useMemo(() => {
        if (mode === 'my') {
            return activities.filter(a => a.isJoined)
        }
        return activities
    }, [activities, mode])

    // Group activities by week and day
    const allWeeks = useMemo(() => {
        return groupActivitiesByWeekAndDay(filteredActivities)
    }, [filteredActivities])

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
            await joinMutation.mutateAsync(activityId)
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

    // Calculate total activities count for the current week
    const totalCount = getWeekActivityCount(displayedWeek)
    const hasActivities = totalCount > 0

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 pt-12">
                <Loading text="Загружаем тренировки..." />
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 pt-12">
                <ErrorMessage message={error} onRetry={refetch} />
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <ModeToggle mode={mode} onModeChange={setMode} />
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
                                expandedDays={expandedDays}
                                onToggleExpansion={toggleDayExpansion}
                                onJoinToggle={handleJoinToggle}
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
