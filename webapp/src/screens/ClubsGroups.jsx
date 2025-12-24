import React, { useState, useMemo } from 'react'
import { BottomNav, CreateMenu, ClubCard, GroupCard, LoadingScreen, ErrorScreen, SearchButton } from '../components'
import { ModeToggle } from '../components/home/ModeToggle'
import { SportFilterButton } from '../components/home/SportFilterButton'
import { SportFilterPopup } from '../components/home/SportFilterPopup'
import { useClubs, useGroups, useJoinClub, useJoinGroup } from '../hooks'

export default function ClubsGroups() {
    const { data: clubs = [], isLoading: clubsLoading, error: clubsError, refetch: refetchClubs } = useClubs()
    const { data: groups = [], isLoading: groupsLoading, error: groupsError, refetch: refetchGroups } = useGroups()

    const { mutate: joinClub } = useJoinClub()
    const { mutate: joinGroup } = useJoinGroup()

    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [showSearch, setShowSearch] = useState(false)
    const [joinConfirm, setJoinConfirm] = useState(null)

    // Mode and filter state (unified with Home)
    const [mode, setMode] = useState('all') // 'my' | 'all'
    const [selectedSports, setSelectedSports] = useState([])
    const [showSportFilter, setShowSportFilter] = useState(false)

    const loading = clubsLoading || groupsLoading
    const error = clubsError || groupsError

    // Sport filter handlers
    const toggleSport = (sportId) => {
        setSelectedSports(prev =>
            prev.includes(sportId)
                ? prev.filter(id => id !== sportId)
                : [...prev, sportId]
        )
    }

    const clearSportFilters = () => {
        setSelectedSports([])
    }

    // Filter by sport types (if club/group has sportTypes array)
    const filterBySportTypes = (items) => {
        if (selectedSports.length === 0) return items
        return items.filter(item =>
            item.sportTypes?.some(st => selectedSports.includes(st))
        )
    }

    // Filter clubs and groups by mode and sport types
    const filteredClubs = useMemo(() => {
        let result = clubs || []

        // Filter by mode
        if (mode === 'my') {
            result = result.filter(c => c.isMember)
        }

        // Filter by sport types
        result = filterBySportTypes(result)

        return result
    }, [clubs, mode, selectedSports])

    const filteredGroups = useMemo(() => {
        let result = groups || []

        // Filter by mode
        if (mode === 'my') {
            result = result.filter(g => g.isMember)
        }

        // Filter by sport types
        result = filterBySportTypes(result)

        return result
    }, [groups, mode, selectedSports])

    // Separate my vs discover for display
    const myClubs = filteredClubs.filter(c => c.isMember)
    const myGroups = filteredGroups.filter(g => g.isMember)
    const discoverClubs = filteredClubs.filter(c => !c.isMember)
    const discoverGroups = filteredGroups.filter(g => !g.isMember)

    // Total count for display
    const totalCount = filteredClubs.length + filteredGroups.length

    // Filter by search
    const filterBySearch = (items) => {
        if (!searchQuery.trim()) return items
        const query = searchQuery.toLowerCase()
        return items.filter(item =>
            item.name.toLowerCase().includes(query) ||
            (item.parentClub && item.parentClub.toLowerCase().includes(query))
        )
    }

    // Handle join
    const handleJoin = (item) => {
        setJoinConfirm(item)
    }

    const handleJoinConfirm = async () => {
        if (!joinConfirm) return

        try {
            if (joinConfirm.type === 'club') {
                await joinClub(joinConfirm.id)
                refetchClubs()
            } else {
                await joinGroup(joinConfirm.id)
                refetchGroups()
            }
            setJoinConfirm(null)
        } catch (e) {
            console.error('Join failed', e)
        }
    }

    // Join Confirmation Popup
    const JoinConfirmPopup = () => {
        if (!joinConfirm) return null

        const isClub = joinConfirm.type === 'club'

        return (
            <div
                className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center px-4"
                onClick={() => setJoinConfirm(null)}
            >
                <div
                    className="bg-white w-full max-w-sm rounded-2xl p-6"
                    onClick={e => e.stopPropagation()}
                >
                    <div className="text-center mb-6">
                        <span className="text-3xl mb-3 block">{isClub ? '🏆' : '👥'}</span>
                        <h3 className="text-base font-medium text-gray-800 mb-2">
                            {isClub ? 'Вступить в клуб?' : 'Вступить в группу?'}
                        </h3>
                        <p className="text-sm text-gray-500">
                            {isClub
                                ? `Отправить заявку на вступление в ${joinConfirm.name}?`
                                : `Вступить в ${joinConfirm.name}?`
                            }
                        </p>
                    </div>

                    <div className="flex gap-3">
                        <button
                            onClick={() => setJoinConfirm(null)}
                            className="flex-1 py-3 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                        >
                            Нет
                        </button>
                        <button
                            onClick={handleJoinConfirm}
                            className="flex-1 py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
                        >
                            Да
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    if (loading) return <LoadingScreen text="Загружаем клубы..." />
    if (error) return <ErrorScreen message={error} onRetry={() => { refetchClubs(); refetchGroups(); }} />

    // Apply search filter to displayed items
    const displayedMyClubs = filterBySearch(myClubs)
    const displayedMyGroups = filterBySearch(myGroups)
    const displayedDiscoverClubs = filterBySearch(discoverClubs)
    const displayedDiscoverGroups = filterBySearch(discoverGroups)

    const hasAnyItems = displayedMyClubs.length > 0 || displayedMyGroups.length > 0 ||
        displayedDiscoverClubs.length > 0 || displayedDiscoverGroups.length > 0

    // Main View
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
            {/* Header - unified with Home */}
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
                            placeholder="Поиск клубов и групп..."
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
                        <ModeToggle mode={mode} onModeChange={setMode} />
                        <div className="flex items-center gap-2">
                            <SearchButton onClick={() => setShowSearch(true)} />
                            <SportFilterButton
                                selectedCount={selectedSports.length}
                                onClick={() => setShowSportFilter(true)}
                            />
                            <span className="text-sm text-gray-400">{totalCount}</span>
                        </div>
                    </>
                )}
            </div>

            {/* Sport Filter Popup */}
            <SportFilterPopup
                isOpen={showSportFilter}
                onClose={() => setShowSportFilter(false)}
                selectedSports={selectedSports}
                onToggle={toggleSport}
                onClear={clearSportFilters}
            />

            {/* Content */}
            <div className="flex-1 overflow-auto px-4 py-4">
                {/* Search empty hint */}
                {showSearch && !searchQuery.trim() && (
                    <p className="text-sm text-gray-400 text-center py-8">
                        Введите название клуба или группы
                    </p>
                )}

                {/* No results */}
                {showSearch && searchQuery.trim() && !hasAnyItems && (
                    <div className="text-center py-8">
                        <span className="text-3xl mb-3 block">🔍</span>
                        <p className="text-sm text-gray-500">Ничего не найдено</p>
                    </div>
                )}

                {/* My clubs and groups */}
                {(displayedMyClubs.length > 0 || displayedMyGroups.length > 0) && (
                    <div className="mb-6">
                        <p className="text-sm text-gray-500 mb-3">Мои</p>

                        {displayedMyClubs.map(club => (
                            <ClubCard key={club.id} club={club} />
                        ))}

                        {displayedMyGroups.map(group => (
                            <GroupCard key={group.id} group={group} />
                        ))}
                    </div>
                )}

                {/* Discover */}
                {(displayedDiscoverClubs.length > 0 || displayedDiscoverGroups.length > 0) && (
                    <div>
                        <p className="text-sm text-gray-500 mb-3">Найти ещё</p>

                        {displayedDiscoverClubs.map(club => (
                            <ClubCard
                                key={club.id}
                                club={club}
                                showJoinButton
                                onJoin={handleJoin}
                            />
                        ))}

                        {displayedDiscoverGroups.map(group => (
                            <GroupCard
                                key={group.id}
                                group={group}
                                showJoinButton
                                onJoin={handleJoin}
                            />
                        ))}
                    </div>
                )}

                {/* Empty state - only show when not searching */}
                {!showSearch && !hasAnyItems && (
                    <div className="text-center py-12">
                        <span className="text-4xl mb-4 block">👥</span>
                        <h2 className="text-base text-gray-700 mb-2">Пока нет клубов</h2>
                        <p className="text-sm text-gray-400 mb-6">Создай свой или найди по ссылке</p>
                        <button
                            onClick={() => setShowCreateMenu(true)}
                            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                        >
                            Создать клуб →
                        </button>
                    </div>
                )}
            </div>

            {/* Bottom Navigation - Fixed */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto">
                <BottomNav onCreateClick={() => setShowCreateMenu(true)} />
            </div>

            <CreateMenu isOpen={showCreateMenu} onClose={() => setShowCreateMenu(false)} />
            <JoinConfirmPopup />
        </div>
    )
}
