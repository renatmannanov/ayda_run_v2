import React, { useState } from 'react'
import { BottomNav, CreateMenu, ClubCard, GroupCard, LoadingScreen, ErrorScreen } from '../components'
import { useClubs, useGroups, useJoinClub, useJoinGroup } from '../hooks'

export default function ClubsGroups() {
    const { data: clubs = [], loading: clubsLoading, error: clubsError, refetch: refetchClubs } = useClubs()
    const { data: groups = [], loading: groupsLoading, error: groupsError, refetch: refetchGroups } = useGroups()

    const { mutate: joinClub } = useJoinClub()
    const { mutate: joinGroup } = useJoinGroup()

    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')
    const [showSearch, setShowSearch] = useState(false)
    const [joinConfirm, setJoinConfirm] = useState(null)

    const loading = clubsLoading || groupsLoading
    const error = clubsError || groupsError

    // Get my clubs and groups
    const myClubs = (clubs || []).filter(c => c.isMember)
    const myGroups = (groups || []).filter(g => g.isMember)

    // Get discover items
    const discoverClubs = (clubs || []).filter(c => !c.isMember)
    const discoverGroups = (groups || []).filter(g => !g.isMember)

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

    // Search Header
    const SearchHeader = () => (
        <div className="bg-white border-b border-gray-200 px-4 py-3">
            <div className="flex items-center gap-3">
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
        </div>
    )

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

    if (loading && !showSearch) return <LoadingScreen text="Загружаем клубы..." />
    if (error) return <ErrorScreen message={error} onRetry={() => { refetchClubs(); refetchGroups(); }} />

    // Search Results View
    if (showSearch) {
        const filteredClubs = filterBySearch([...clubs])
        const filteredGroups = filterBySearch([...groups])
        const hasResults = filteredClubs.length > 0 || filteredGroups.length > 0

        return (
            <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
                <SearchHeader />

                <div className="flex-1 overflow-auto px-4 py-4">
                    {!searchQuery.trim() ? (
                        <p className="text-sm text-gray-400 text-center py-8">
                            Введите название клуба или группы
                        </p>
                    ) : !hasResults ? (
                        <div className="text-center py-8">
                            <span className="text-3xl mb-3 block">🔍</span>
                            <p className="text-sm text-gray-500">Ничего не найдено</p>
                        </div>
                    ) : (
                        <>
                            {filteredClubs.length > 0 && (
                                <div className="mb-6">
                                    <p className="text-sm text-gray-500 mb-3">Клубы</p>
                                    {filteredClubs.map(club => (
                                        <ClubCard
                                            key={club.id}
                                            club={club}
                                            showJoinButton={!club.isMember}
                                            onJoin={handleJoin}
                                        />
                                    ))}
                                </div>
                            )}

                            {filteredGroups.length > 0 && (
                                <div>
                                    <p className="text-sm text-gray-500 mb-3">Группы</p>
                                    {filteredGroups.map(group => (
                                        <GroupCard
                                            key={group.id}
                                            group={group}
                                            showJoinButton={!group.isMember}
                                            onJoin={handleJoin}
                                        />
                                    ))}
                                </div>
                            )}
                        </>
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

    // Main View
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <h1 className="text-base font-medium text-gray-800">Клубы и группы</h1>
                <button
                    onClick={() => setShowSearch(true)}
                    className="text-gray-400 hover:text-gray-600 text-lg"
                >
                    🔍
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto px-4 py-4">
                {/* My clubs and groups */}
                {(myClubs.length > 0 || myGroups.length > 0) && (
                    <div className="mb-6">
                        <p className="text-sm text-gray-500 mb-3">Мои</p>

                        {myClubs.map(club => (
                            <ClubCard key={club.id} club={club} />
                        ))}

                        {myGroups.map(group => (
                            <GroupCard key={group.id} group={group} />
                        ))}
                    </div>
                )}

                {/* Discover */}
                {(discoverClubs.length > 0 || discoverGroups.length > 0) && (
                    <div>
                        <p className="text-sm text-gray-500 mb-3">Найти ещё</p>

                        {discoverClubs.map(club => (
                            <ClubCard
                                key={club.id}
                                club={club}
                                showJoinButton
                                onJoin={handleJoin}
                            />
                        ))}

                        {discoverGroups.map(group => (
                            <GroupCard
                                key={group.id}
                                group={group}
                                showJoinButton
                                onJoin={handleJoin}
                            />
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {myClubs.length === 0 && myGroups.length === 0 && discoverClubs.length === 0 && discoverGroups.length === 0 && (
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
