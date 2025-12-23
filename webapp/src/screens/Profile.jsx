import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BottomNav, CreateMenu } from '../components'
import { Avatar } from '../components/ui'
import { StravaLink, ClubGroupCard } from '../components/profile'
import { usersApi, tg } from '../api'
import { useUser } from '../contexts/UserContext'
import { useClubs, useGroups } from '../hooks'
import { SPORT_TYPES } from '../constants/sports'

export default function Profile() {
    const navigate = useNavigate()
    const { user: userProfile } = useUser()

    // User info (merge TG data, Backend data)
    const user = {
        name: userProfile?.firstName || tg.user?.first_name || 'Бегун',
        username: userProfile?.username || tg.user?.username || 'runner',
        photo: userProfile?.photo || null,
        stravaLink: userProfile?.stravaLink || null,
        ...tg.user,
        ...userProfile
    }

    // Fetch my clubs and groups
    const { data: clubs = [] } = useClubs()
    const { data: groups = [] } = useGroups()

    const myClubs = (clubs || []).filter(c => c.isMember)
    const myGroups = (groups || []).filter(g => g.isMember)

    // Combine clubs and groups for horizontal scroll
    const myOrganizations = [
        ...myClubs.map(c => ({ ...c, type: 'club' })),
        ...myGroups.map(g => ({ ...g, type: 'group' }))
    ]

    const [showCreateMenu, setShowCreateMenu] = useState(false)

    // Stats preview (just the percentage)
    const [statsPreview, setStatsPreview] = useState(null)
    useEffect(() => {
        usersApi.getStats('month')
            .then(data => setStatsPreview(data))
            .catch(() => {})
    }, [])

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

    const handleOrganizationClick = (item) => {
        if (item.type === 'club') {
            navigate(`/club/${item.id}`)
        } else {
            navigate(`/group/${item.id}`)
        }
    }

    return (
        <div className="h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
                <h1 className="text-base font-medium text-gray-800">Профиль</h1>
            </div>

            {/* Content */}
            <div className="flex-1 px-4 py-3 pb-20">
                {/* User Info Card - New Layout */}
                <div className="bg-white rounded-2xl p-4 mb-3">
                    <div className="flex items-start gap-4">
                        {/* Avatar - bigger, left aligned */}
                        <div className="flex-shrink-0">
                            <Avatar
                                src={user.photo}
                                name={`${user.first_name || user.name} ${user.last_name || ''}`}
                                size="2xl"
                            />
                        </div>

                        {/* Info - right side */}
                        <div className="flex-1 min-w-0 pt-1">
                            <h2 className="text-lg font-medium text-gray-800 truncate">
                                {user.first_name || user.name} {user.last_name || ''}
                            </h2>
                            <p className="text-sm text-gray-400">
                                {user.username ? `@${user.username}` : ''}
                            </p>

                            {/* Sports Icons */}
                            {sportIcons && sportIcons.length > 0 && (
                                <div className="flex gap-1 mt-1.5">
                                    {sportIcons.map((icon, idx) => (
                                        <span key={idx} className="text-lg">{icon}</span>
                                    ))}
                                </div>
                            )}

                            {/* Strava Link */}
                            <div className="mt-2">
                                <StravaLink
                                    url={user.stravaLink}
                                    onAdd={() => navigate('/settings')}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Clubs & Groups - Horizontal Scroll */}
                {myOrganizations.length > 0 && (
                    <div className="bg-white rounded-2xl p-3 mb-3">
                        <p className="text-sm font-medium text-gray-800 mb-3">
                            Клубы и группы ({myOrganizations.length})
                        </p>
                        <div className="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1">
                            {myOrganizations.map(item => (
                                <ClubGroupCard
                                    key={`${item.type}-${item.id}`}
                                    item={item}
                                    onClick={() => handleOrganizationClick(item)}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {/* Stats & Settings Links */}
                <div className="bg-white rounded-2xl overflow-hidden">
                    {/* Statistics Link */}
                    <button
                        onClick={() => navigate('/statistics')}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors border-b border-gray-100"
                    >
                        <div className="flex items-center gap-3">
                            <span className="text-lg">📊</span>
                            <span className="text-sm font-medium text-gray-800">Статистика</span>
                        </div>
                        <div className="flex items-center gap-2">
                            {statsPreview && (
                                <span className="text-sm text-gray-400">
                                    {statsPreview.attendance_rate}%
                                </span>
                            )}
                            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                            </svg>
                        </div>
                    </button>

                    {/* Settings Link */}
                    <button
                        onClick={() => navigate('/settings')}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <span className="text-lg">⚙️</span>
                            <span className="text-sm font-medium text-gray-800">Настройки</span>
                        </div>
                        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>

                {/* App info */}
                <div className="mt-8 text-center">
                    <p className="text-xs text-gray-400">Ayda Run v2.0</p>
                    <p className="text-xs text-gray-400 mt-0.5">Made with ❤️ in Almaty</p>
                </div>
            </div>

            {/* Bottom Navigation - Fixed */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto">
                <BottomNav onCreateClick={() => setShowCreateMenu(true)} />
            </div>

            {/* Create Menu */}
            <CreateMenu isOpen={showCreateMenu} onClose={() => setShowCreateMenu(false)} />
        </div>
    )
}
