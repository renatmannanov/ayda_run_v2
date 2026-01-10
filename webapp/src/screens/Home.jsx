import React, { useState, useEffect, useMemo } from 'react'
import { useLocation, useSearchParams, useNavigate } from 'react-router-dom'
import { BottomBar, CreateMenu, Loading, ErrorMessage, EmptyState, SearchButton } from '../components'
import { DaySection } from '../components/home/DaySection'
import { ModeToggle } from '../components/home/ModeToggle'
import { SportFilterButton } from '../components/home/SportFilterButton'
import { ActivityFilterPopup } from '../components/home/ActivityFilterPopup'
import { WelcomeBanner } from '../components/home/WelcomeBanner'
import { useActivities, useJoinActivity, useClubs, useGroups } from '../hooks'
import { groupActivitiesByWeekAndDay, getWeekRangeText, getWeekActivityCount } from '../utils/weekUtils'

export default function Home() {
    const location = useLocation()
    const [searchParams, setSearchParams] = useSearchParams()
    const navigate = useNavigate()

    // Initialize mode from URL param, default to 'my'
    const modeFromUrl = searchParams.get('mode')
    const mode = modeFromUrl === 'all' ? 'all' : 'my'

    // Update mode in URL without adding to history
    const setMode = (newMode) => {
        const newParams = new URLSearchParams(searchParams)
        if (newMode === 'all') {
            newParams.set('mode', 'all')
        } else {
            newParams.delete('mode')
        }
        setSearchParams(newParams, { replace: true })
    }

    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [currentWeekIndex, setCurrentWeekIndex] = useState(null)
    const [expandedDays, setExpandedDays] = useState({})

    // Filter state
    const [selectedSports, setSelectedSports] = useState([])
    const [selectedClubs, setSelectedClubs] = useState([])
    const [selectedGroups, setSelectedGroups] = useState([])
    const [showFilterPopup, setShowFilterPopup] = useState(false)
    const [filterLabel, setFilterLabel] = useState(null) // Label for active filter (e.g., club/group name)

    // Apply filter from URL params (from club/group detail screen)
    useEffect(() => {
        const clubId = searchParams.get('clubId')
        const clubName = searchParams.get('clubName')
        const groupId = searchParams.get('groupId')
        const groupName = searchParams.get('groupName')

        if (clubId) {
            // Keep as string - IDs are UUIDs, not integers
            setSelectedClubs([clubId])
            setFilterLabel(clubName || 'Клуб')
            // Clear filter params but preserve mode
            const newParams = new URLSearchParams()
            if (searchParams.get('mode')) {
                newParams.set('mode', searchParams.get('mode'))
            }
            setSearchParams(newParams, { replace: true })
        } else if (groupId) {
            // Keep as string - IDs are UUIDs, not integers
            setSelectedGroups([groupId])
            setFilterLabel(groupName || 'Группа')
            // Clear filter params but preserve mode
            const newParams = new URLSearchParams()
            if (searchParams.get('mode')) {
                newParams.set('mode', searchParams.get('mode'))
            }
            setSearchParams(newParams, { replace: true })
        }
    }, [searchParams, setSearchParams])

    // Search state
    const [searchQuery, setSearchQuery] = useState('')
    const [showSearch, setShowSearch] = useState(false)

    // Swipe state
    const [touchStart, setTouchStart] = useState(null)
    const [touchEnd, setTouchEnd] = useState(null)
    const minSwipeDistance = 50

    // Fetch clubs and groups for filter
    const { data: clubs = [] } = useClubs()
    const { data: groups = [] } = useGroups()

    // My clubs and groups (for filter options)
    const myClubs = useMemo(() => (clubs || []).filter(c => c.isMember), [clubs])
    const myGroups = useMemo(() => (groups || []).filter(g => g.isMember), [groups])


    // Build API filters (only sport_types is supported by API)
    const apiFilters = useMemo(() => {
        const filters = {}
        if (selectedSports.length > 0) {
            filters.sport_types = selectedSports.join(',')
        }
        return filters
    }, [selectedSports])

    // Fetch activities with filters
    const { data: activities = [], isLoading: loading, error, refetch } = useActivities(apiFilters)

    // Join/Leave mutation
    const joinMutation = useJoinActivity()

    // Filter activities by mode, clubs/groups, and search
    const filteredActivities = useMemo(() => {
        let result = activities

        // Filter by mode
        if (mode === 'my') {
            result = result.filter(a => a.isJoined)
        }

        // Filter by selected clubs (client-side)
        if (selectedClubs.length > 0) {
            result = result.filter(a => a.clubId && selectedClubs.includes(a.clubId))
        }

        // Filter by selected groups (client-side)
        if (selectedGroups.length > 0) {
            result = result.filter(a => a.groupId && selectedGroups.includes(a.groupId))
        }

        // Filter by search query
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase()
            result = result.filter(a =>
                a.title?.toLowerCase().includes(query) ||
                a.location?.toLowerCase().includes(query) ||
                a.club?.toLowerCase().includes(query) ||
                a.group?.toLowerCase().includes(query)
            )
        }

        return result
    }, [activities, mode, selectedClubs, selectedGroups, searchQuery])

    // Group activities by week and day
    const allWeeks = useMemo(() => {
        return groupActivitiesByWeekAndDay(filteredActivities)
    }, [filteredActivities])

    // Track previous mode to detect changes
    const [prevMode, setPrevMode] = useState(mode)

    // Reset week index when mode changes
    useEffect(() => {
        if (mode !== prevMode) {
            setPrevMode(mode)
            // Reset to current week on mode change
            if (allWeeks.length > 0) {
                const currentWeekIdx = allWeeks.findIndex(w => w.weekNumber === 0)
                setCurrentWeekIndex(currentWeekIdx >= 0 ? currentWeekIdx : 0)
            }
        }
    }, [mode, prevMode, allWeeks])

    // Set initial week index or fix invalid index
    useEffect(() => {
        if (allWeeks.length > 0) {
            const isInvalidIndex = currentWeekIndex === null || currentWeekIndex >= allWeeks.length
            if (isInvalidIndex) {
                const currentWeekIdx = allWeeks.findIndex(w => w.weekNumber === 0)
                setCurrentWeekIndex(currentWeekIdx >= 0 ? currentWeekIdx : 0)
            }
        }
    }, [allWeeks, currentWeekIndex])

    // Get currently displayed week - use safe fallback to avoid flicker
    const displayedWeek = useMemo(() => {
        if (allWeeks.length === 0) return null
        if (currentWeekIndex !== null && allWeeks[currentWeekIndex]) {
            return allWeeks[currentWeekIndex]
        }
        // Fallback: find current week to avoid showing "empty"
        const currentWeekIdx = allWeeks.findIndex(w => w.weekNumber === 0)
        return allWeeks[currentWeekIdx >= 0 ? currentWeekIdx : 0] || null
    }, [allWeeks, currentWeekIndex])

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

    // Toggle join (no explicit refetch needed - optimistic update + invalidation handles it)
    const handleJoinToggle = async (activityId) => {
        try {
            await joinMutation.mutateAsync(activityId)
        } catch (e) {
            // Error handled by useMutation
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

    // Filter handlers
    const toggleSport = (sportId) => {
        setSelectedSports(prev =>
            prev.includes(sportId)
                ? prev.filter(id => id !== sportId)
                : [...prev, sportId]
        )
    }

    const toggleClub = (clubId) => {
        setSelectedClubs(prev =>
            prev.includes(clubId)
                ? prev.filter(id => id !== clubId)
                : [...prev, clubId]
        )
    }

    const toggleGroup = (groupId) => {
        setSelectedGroups(prev =>
            prev.includes(groupId)
                ? prev.filter(id => id !== groupId)
                : [...prev, groupId]
        )
    }

    const clearAllFilters = () => {
        setSelectedSports([])
        setSelectedClubs([])
        setSelectedGroups([])
        setFilterLabel(null)
    }

    // Total active filters count
    const activeFiltersCount = selectedSports.length + selectedClubs.length + selectedGroups.length

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
                {showSearch ? (
                    <div className="flex items-center gap-3 flex-1">
                        <button
                            onClick={() => {
                                setShowSearch(false)
                                setSearchQuery('')
                            }}
                            className="text-gray-500 hover:text-gray-700"
                        >
                            ←
                        </button>
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Поиск тренировок..."
                            className="flex-1 text-sm text-gray-800 placeholder-gray-400 outline-none"
                            autoFocus
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                ✕
                            </button>
                        )}
                    </div>
                ) : (
                    <>
                        <ModeToggle mode={mode} onModeChange={setMode} title="Активности" />
                        <div className="flex items-center gap-2">
                            <SearchButton onClick={() => setShowSearch(true)} />
                            <SportFilterButton
                                selectedCount={activeFiltersCount}
                                onClick={() => setShowFilterPopup(true)}
                            />
                            <span className="text-sm text-gray-400 min-w-[20px] text-right">{totalCount}</span>
                        </div>
                    </>
                )}
            </div>

            {/* Active filter label (from club/group navigation) */}
            {filterLabel && (
                <div className="bg-gray-100 px-4 py-2 flex items-center justify-between">
                    <span className="text-sm text-gray-600">Фильтр: {filterLabel}</span>
                    <button
                        onClick={clearAllFilters}
                        className="text-sm text-gray-400 hover:text-gray-600"
                    >
                        ✕ Сбросить
                    </button>
                </div>
            )}

            {/* Activity Filter Popup */}
            <ActivityFilterPopup
                isOpen={showFilterPopup}
                onClose={() => setShowFilterPopup(false)}
                myClubs={myClubs}
                myGroups={myGroups}
                selectedClubs={selectedClubs}
                selectedGroups={selectedGroups}
                onToggleClub={toggleClub}
                onToggleGroup={toggleGroup}
                selectedSports={selectedSports}
                onToggleSport={toggleSport}
                onClear={clearAllFilters}
            />

            {/* Content - with swipe */}
            <div
                className="flex-1 overflow-auto px-4 py-4"
                onTouchStart={onTouchStart}
                onTouchMove={onTouchMove}
                onTouchEnd={onTouchEnd}
            >
                {/* Welcome banner for new users with clubs but no activities */}
                {mode === 'my' && !hasActivities && myClubs.length > 0 && (
                    <WelcomeBanner club={myClubs[0]} />
                )}

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
                        description={mode === 'my' ? "Создай свои тренировки или выбери из активностей сообщества" : "Нет предстоящих тренировок"}
                        actionText={mode === 'my' ? "Смотреть активности сообщества" : null}
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
                        className="flex items-center justify-between select-none"
                        onTouchStart={onTouchStart}
                        onTouchMove={onTouchMove}
                        onTouchEnd={onTouchEnd}
                    >
                        {/* < - previous week */}
                        <button
                            onClick={goToPreviousWeek}
                            disabled={!canGoPrevious}
                            className={`p-2 transition-colors ${canGoPrevious ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                            </svg>
                        </button>

                        {/* Center - Week info (clickable to go to current) */}
                        <button
                            onClick={goToCurrentWeek}
                            disabled={displayedWeek?.weekNumber === 0}
                            className="text-center flex-1"
                        >
                            <p className="text-sm font-medium text-gray-800">{getWeekLabel()}</p>
                            <p className="text-xs text-gray-400">{getWeekRangeText(displayedWeek)}</p>
                        </button>

                        {/* > - next week */}
                        <button
                            onClick={goToNextWeek}
                            disabled={!canGoNext}
                            className={`p-2 transition-colors ${canGoNext ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
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
