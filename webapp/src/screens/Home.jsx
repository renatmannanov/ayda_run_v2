import React, { useState, useEffect, useMemo } from 'react'
import { BottomBar, CreateMenu, Loading, ErrorMessage, EmptyState } from '../components'
import { DaySection } from '../components/home/DaySection'
import { ModeToggle } from '../components/home/ModeToggle'
import { useActivities, useJoinActivity } from '../hooks'
import { groupActivitiesByWeekAndDay, getWeekRangeText, getWeekActivityCount } from '../utils/weekUtils'

export default function Home() {
    const [mode, setMode] = useState('all') // 'my' | 'all'
    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [currentWeekIndex, setCurrentWeekIndex] = useState(null)
    const [expandedDays, setExpandedDays] = useState({})

    // Swipe state
    const [touchStart, setTouchStart] = useState(null)
    const [touchEnd, setTouchEnd] = useState(null)
    const minSwipeDistance = 50

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

    // Find current week index for "go to current" buttons
    const currentWeekIdx = allWeeks.findIndex(w => w.weekNumber === 0)
    const isInFuture = displayedWeek && displayedWeek.weekNumber > 0
    const isInPast = displayedWeek && displayedWeek.weekNumber < 0

    // Go to current week
    const goToCurrentWeek = () => {
        if (currentWeekIdx >= 0) {
            setCurrentWeekIndex(currentWeekIdx)
        }
    }

    // Swipe handlers
    const onTouchStart = (e) => {
        setTouchEnd(null)
        setTouchStart(e.targetTouches[0].clientX)
    }

    const onTouchMove = (e) => {
        setTouchEnd(e.targetTouches[0].clientX)
    }

    const onTouchEnd = () => {
        if (!touchStart || !touchEnd) return
        const distance = touchStart - touchEnd
        const isLeftSwipe = distance > minSwipeDistance
        const isRightSwipe = distance < -minSwipeDistance

        if (isLeftSwipe && canGoNext) {
            goToNextWeek()
        }
        if (isRightSwipe && canGoPrevious) {
            goToPreviousWeek()
        }
    }

    // Dynamic week label
    const getWeekLabel = () => {
        if (!displayedWeek) return ''
        const weekNum = displayedWeek.weekNumber
        if (weekNum === 0) return 'Текущая неделя'
        if (weekNum === 1) return 'Следующая неделя'
        if (weekNum === -1) return 'Прошлая неделя'
        if (weekNum > 1) return `Через ${weekNum} нед.`
        return `${Math.abs(weekNum)} нед. назад`
    }

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
        <div className="min-h-screen bg-gray-50 flex flex-col pb-40">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <ModeToggle mode={mode} onModeChange={setMode} />
                <span className="text-sm text-gray-400">{totalCount}</span>
            </div>

            {/* Content - with swipe */}
            <div
                className="flex-1 overflow-auto px-4 py-4"
                onTouchStart={onTouchStart}
                onTouchMove={onTouchMove}
                onTouchEnd={onTouchEnd}
            >
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

            {/* Bottom Bar with Week Navigation */}
            <BottomBar
                onCreateClick={() => setShowCreateMenu(true)}
                showAction={!!displayedWeek}
                action={
                    <div
                        className="flex items-center justify-between bg-gray-100 rounded-xl px-3 py-2 select-none"
                        onTouchStart={onTouchStart}
                        onTouchMove={onTouchMove}
                        onTouchEnd={onTouchEnd}
                    >
                        {/* Left buttons: << and < */}
                        <div className="flex flex-col items-center gap-1 -ml-1">
                            {/* < - previous week */}
                            <button
                                onClick={goToPreviousWeek}
                                disabled={!canGoPrevious}
                                className={`p-1 transition-colors ${canGoPrevious ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                                </svg>
                            </button>
                            {/* << - go to current (active when in future) */}
                            <button
                                onClick={goToCurrentWeek}
                                disabled={!isInFuture}
                                className={`p-1 transition-colors ${isInFuture ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7M18 19l-7-7 7-7" />
                                </svg>
                            </button>
                        </div>

                        {/* Center - Week info */}
                        <div className="text-center flex-1">
                            <p className="text-sm font-medium text-gray-800">{getWeekLabel()}</p>
                            <p className="text-xs text-gray-400">{getWeekRangeText(displayedWeek)}</p>
                        </div>

                        {/* Right buttons: > and >> */}
                        <div className="flex flex-col items-center gap-1 -mr-1">
                            {/* > - next week */}
                            <button
                                onClick={goToNextWeek}
                                disabled={!canGoNext}
                                className={`p-1 transition-colors ${canGoNext ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                                </svg>
                            </button>
                            {/* >> - go to current (active when in past) */}
                            <button
                                onClick={goToCurrentWeek}
                                disabled={!isInPast}
                                className={`p-1 transition-colors ${isInPast ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M6 5l7 7-7 7" />
                                </svg>
                            </button>
                        </div>
                    </div>
                }
            />

            {/* Create Menu */}
            <CreateMenu
                isOpen={showCreateMenu}
                onClose={() => setShowCreateMenu(false)}
            />
        </div>
    )
}
