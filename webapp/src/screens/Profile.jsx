import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BottomNav, CreateMenu, LoadingScreen, ErrorScreen } from '../components'
import { Avatar } from '../components/ui'
import { usersApi, tg } from '../api'
import { useApi, useClubs, useGroups } from '../hooks'
import { SPORT_TYPES } from '../constants/sports'

export default function Profile() {
    const navigate = useNavigate()

    // Fetch user profile from backend
    const { data: userProfile } = useApi(usersApi.getMe)

    // User info (merge TG data, Backend data, and defaults)
    const user = {
        name: userProfile?.firstName || tg.user?.first_name || 'Бегун',
        username: userProfile?.username || tg.user?.username || 'runner',
        photo: userProfile?.photo || null,
        ...tg.user, // TG data takes precedence if available
        ...userProfile // Backend data overwrites if available
    }

    // Fetch my clubs and groups
    // Optimization: backend should provided /me/clubs or we filter list.
    // For now, filtering the full list since dataset is small.
    const { data: clubs = [] } = useClubs()
    const { data: groups = [] } = useGroups()

    const myClubs = (clubs || []).filter(c => c.isMember)
    const myGroups = (groups || []).filter(g => g.isMember)

    const [showStats, setShowStats] = useState(false)
    const [showCreateMenu, setShowCreateMenu] = useState(false)

    // Fetch user stats from backend
    const { data: statsData } = useApi(usersApi.getStats)

    const stats = {
        totalActivities: statsData?.totalActivities || 0,
        attended: statsData?.completedActivities || 0,
        missed: (statsData?.totalActivities || 0) - (statsData?.completedActivities || 0),
        attendanceRate: statsData?.attendanceRate || 0
    }

    // Parse user's preferred sports and get icons
    const getUserSportIcons = () => {
        try {
            if (!userProfile?.preferredSports) return null
            const sports = JSON.parse(userProfile.preferredSports)
            return sports.map(sportId => {
                const sport = SPORT_TYPES.find(s => s.id === sportId)
                return sport?.icon || null
            }).filter(Boolean)
        } catch {
            return null
        }
    }

    const sportIcons = getUserSportIcons()

    // Mini Club Card
    const MiniClubCard = ({ club }) => (
        <button
            onClick={() => navigate(`/club/${club.id}`)}
            className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-left hover:bg-gray-100 transition-colors w-full"
        >
            <div className="flex items-center gap-2 mb-1">
                <span>🏆</span>
                <span className="text-sm text-gray-800 font-medium truncate w-full">{club.name}</span>
            </div>
            <p className="text-xs text-gray-500">{club.members} чел</p>
        </button>
    )

    // Mini Group Card
    const MiniGroupCard = ({ group }) => (
        <button
            onClick={() => navigate(`/group/${group.id}`)}
            className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-left hover:bg-gray-100 transition-colors w-full"
        >
            <div className="flex items-center gap-2 mb-1">
                <span>👥</span>
                <span className="text-sm text-gray-800 font-medium truncate w-full">
                    {group.name}
                    {group.parentClub && <span className="text-gray-400 font-normal"> / {group.parentClub}</span>}
                </span>
            </div>
            <p className="text-xs text-gray-500">{group.members} чел</p>
        </button>
    )

    // Stats Modal
    const StatsModal = () => (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center px-4"
            onClick={() => setShowStats(false)}
        >
            <div
                className="bg-white w-full max-w-sm rounded-2xl p-6"
                onClick={e => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-base font-medium text-gray-800">Статистика</h3>
                    <button
                        onClick={() => setShowStats(false)}
                        className="text-gray-400 hover:text-gray-600 text-xl"
                    >
                        ✕
                    </button>
                </div>

                <div className="space-y-4">
                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                        <span className="text-sm text-gray-600">Всего тренировок</span>
                        <span className="text-sm font-medium text-gray-800">{stats.totalActivities}</span>
                    </div>

                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                        <span className="text-sm text-gray-600">Посещено</span>
                        <span className="text-sm font-medium text-green-600">{stats.attended}</span>
                    </div>

                    <div className="flex justify-between items-center py-2 border-b border-gray-100">
                        <span className="text-sm text-gray-600">Пропущено</span>
                        <span className="text-sm font-medium text-gray-400">{stats.missed}</span>
                    </div>

                    <div className="flex justify-between items-center py-2">
                        <span className="text-sm text-gray-600">Посещаемость</span>
                        <span className="text-sm font-medium text-gray-800">{stats.attendanceRate}%</span>
                    </div>
                </div>

                {/* Progress bar */}
                <div className="mt-6">
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-green-500 rounded-full transition-all"
                            style={{ width: `${stats.attendanceRate}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-400 mt-2 text-center">
                        {stats.attended} из {stats.totalActivities} тренировок
                    </p>
                </div>
            </div>
        </div>
    )

    return (
        <div className="h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
                <h1 className="text-base font-medium text-gray-800">Профиль</h1>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4 pb-28">
                {/* User Info Card */}
                <div className="border border-gray-200 rounded-xl p-6 bg-white mb-4">
                    <div className="flex flex-col items-center text-center">
                        <div className="mb-3">
                            <Avatar
                                src={user.photo}
                                name={`${user.first_name || user.name} ${user.last_name || ''}`}
                                size="xl"
                            />
                        </div>
                        <h2 className="text-lg text-gray-800 font-medium">
                            {user.first_name || user.name} {user.last_name || ''}
                        </h2>
                        <p className="text-sm text-gray-500">
                            {user.username ? `@${user.username}` : ''}
                        </p>
                    </div>
                </div>

                {/* Clubs Section */}
                {myClubs.length > 0 && (
                    <div className="border border-gray-200 rounded-xl p-4 bg-white mb-4">
                        <p className="text-sm text-gray-500 mb-3">Мои клубы ({myClubs.length})</p>
                        <div className="grid grid-cols-2 gap-3">
                            {myClubs.map(club => (
                                <MiniClubCard key={club.id} club={club} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Groups Section */}
                {myGroups.length > 0 && (
                    <div className="border border-gray-200 rounded-xl p-4 bg-white mb-4">
                        <p className="text-sm text-gray-500 mb-3">Мои группы ({myGroups.length})</p>
                        <div className="grid grid-cols-2 gap-3">
                            {myGroups.map(group => (
                                <MiniGroupCard key={group.id} group={group} />
                            ))}
                        </div>
                    </div>
                )}

                {/* Stats & Settings */}
                <div className="border border-gray-200 rounded-xl bg-white overflow-hidden">
                    <button
                        onClick={() => setShowStats(true)}
                        className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100"
                    >
                        <span className="text-lg">📊</span>
                        <span className="text-sm text-gray-700 flex-1 text-left">Статистика</span>
                        <span className="text-sm text-gray-400">{stats.attendanceRate}%</span>
                        <span className="text-gray-300">→</span>
                    </button>

                    <button className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100">
                        <span className="text-lg">🎨</span>
                        <span className="text-sm text-gray-700 flex-1 text-left">Виды спорта</span>
                        {sportIcons && sportIcons.length > 0 ? (
                            <div className="flex gap-1">
                                {sportIcons.map((icon, idx) => (
                                    <span key={idx} className="text-lg">{icon}</span>
                                ))}
                            </div>
                        ) : (
                            <span className="text-sm text-gray-400">Не выбрано</span>
                        )}
                        <span className="text-gray-300">→</span>
                    </button>

                    <button className="w-full px-4 py-4 flex items-center gap-3 opacity-40 cursor-not-allowed">
                        <span className="text-lg">⚙️</span>
                        <span className="text-sm text-gray-700 flex-1 text-left">Настройки</span>
                        <span className="text-gray-300">→</span>
                    </button>
                </div>

                {/* App info */}
                <div className="mt-6 text-center">
                    <p className="text-xs text-gray-400">Ayda Run v2.0</p>
                    <p className="text-xs text-gray-300 mt-1">Made with ❤️ in Almaty</p>
                </div>
            </div>

            {/* Bottom Navigation - Fixed */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto">
                <BottomNav onCreateClick={() => setShowCreateMenu(true)} />
            </div>

            {/* Stats Modal */}
            {showStats && <StatsModal />}

            {/* Create Menu */}
            <CreateMenu isOpen={showCreateMenu} onClose={() => setShowCreateMenu(false)} />
        </div>
    )
}
