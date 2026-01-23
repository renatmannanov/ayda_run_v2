import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { CreateMenu, ParticipantsSheet, MiniActivityCard, LoadingScreen, ErrorScreen, Button, BottomBar } from '../components'
import { Avatar, AvatarStack, Linkify } from '../components/ui'
import {
    useClub,
    useGroup,
    useActivities,
    useJoinClub,
    useJoinGroup,
    useGroups, // To fetch groups for a club
    useClubMembers,
    useGroupMembers,
    useDeleteClub,
    useDeleteGroup,
    tg // for confirmations
} from '../hooks'
import { clubsApi, groupsApi } from '../api'
import { useToast } from '../contexts/ToastContext'
import { pluralizeMembers, pluralizeGroups } from '../data/sample_data'
import { SPORT_TYPES } from '../constants/sports'

// Helper to get sport icon by id
const getSportIcon = (sportId) => {
    const sport = SPORT_TYPES.find(s => s.id === sportId)
    return sport?.icon || null
}

export default function ClubGroupDetail({ type = 'club' }) {
    const { id } = useParams()
    const navigate = useNavigate()
    const { showToast } = useToast()

    const isClub = type === 'club'

    // Fetch item data
    // ALWAYS call both hooks to respect React Rules of Hooks
    // Pass null if not applicable (hooks in useApi.js are now guarded)
    const {
        data: clubData,
        isLoading: clubLoading,
        error: clubError,
        refetch: refetchClub
    } = useClub(isClub ? id : null)

    const {
        data: groupData,
        isLoading: groupLoading,
        error: groupError,
        refetch: refetchGroup
    } = useGroup(!isClub ? id : null)

    const item = isClub ? clubData : groupData
    const loading = isClub ? clubLoading : groupLoading
    const error = isClub ? clubError : groupError
    const refetch = isClub ? refetchClub : refetchGroup

    // Fetch groups if it's a club (to show subgroups)
    const { data: clubGroups = [] } = useGroups(isClub ? id : null)

    // Fetch activities for this club/group
    const filters = isClub ? { club_id: id } : { group_id: id }
    const {
        data: activitiesData,
        isLoading: activitiesLoading
    } = useActivities(filters)

    const activities = activitiesData || []

    // Mutations
    const { mutate: joinClub, loading: joiningClub } = useJoinClub()
    const { mutate: joinGroup, loading: joiningGroup } = useJoinGroup()
    const { mutate: deleteClub } = useDeleteClub()
    const { mutate: deleteGroup } = useDeleteGroup()

    const [showParticipants, setShowParticipants] = useState(false)
    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [showGearMenu, setShowGearMenu] = useState(false) // State for gear menu popup

    // Fetch members
    // Check if club or group, and use appropriate hook
    const { data: clubMembers } = useClubMembers(isClub ? id : null)
    const { data: groupMembers } = useGroupMembers(!isClub ? id : null)

    // Combine list (only one will be populated)
    const participants = (isClub ? clubMembers : groupMembers) || []

    const upcomingActivities = activities.filter(a => !a.isPast)

    const toggleMembership = async () => {
        try {
            // Check if entity is closed - need to send request instead of direct join
            if (!item.isOpen) {
                // Closed entity - send join request
                if (isClub) {
                    await clubsApi.requestJoin(id)
                } else {
                    await groupsApi.requestJoin(id)
                }
                showToast('Заявка отправлена')
            } else {
                // Open entity - direct join
                if (isClub) {
                    await joinClub(id)
                    showToast('Вы вступили в клуб')
                } else {
                    await joinGroup(id)
                    showToast('Вы вступили в группу')
                }
            }
            refetch()
        } catch (e) {
            showToast(e.message || 'Произошла ошибка', 'error')
        }
    }

    const handleDelete = async () => {
        const entityType = isClub ? 'клуб' : 'группу'
        const membersCount = (participants?.length || 1) - 1 // Exclude current user

        // Step 1: Confirm deletion
        tg.showConfirm(`Вы действительно хотите удалить этот ${entityType}?`, (confirmed) => {
            if (!confirmed) return

            // Step 2: Ask about activities
            tg.showConfirm(
                'Удалить связанные тренировки?\n\nCancel = оставить тренировки\nOK = удалить тренировки',
                (deleteActivities) => {
                    // Step 3: Ask about notifications if there are other members
                    if (membersCount > 0) {
                        tg.showConfirm(
                            `Уведомить ${membersCount} участников об удалении?\n\nCancel = не уведомлять\nOK = уведомить`,
                            async (notifyMembers) => {
                                try {
                                    if (isClub) {
                                        await deleteClub({ id, notifyMembers, deleteActivities })
                                    } else {
                                        await deleteGroup({ id, notifyMembers, deleteActivities })
                                    }
                                    navigate('/clubs')
                                } catch (e) {
                                    showToast(e.message || 'Ошибка удаления', 'error')
                                }
                            }
                        )
                    } else {
                        // No other members - just delete
                        const doDelete = async () => {
                            try {
                                if (isClub) {
                                    await deleteClub({ id, notifyMembers: false, deleteActivities })
                                } else {
                                    await deleteGroup({ id, notifyMembers: false, deleteActivities })
                                }
                                navigate('/clubs')
                            } catch (e) {
                                showToast(e.message || 'Ошибка удаления', 'error')
                            }
                        }
                        doDelete()
                    }
                }
            )
        })
    }

    const isAdmin = item?.isAdmin

    if (loading) return <LoadingScreen text={`Загружаем ${isClub ? 'клуб' : 'группу'}...`} />
    if (error) return <ErrorScreen message={error} onRetry={refetch} />
    if (!item) return <ErrorScreen message="Не найдено" />

    // Gear Menu Popup (Sheet Style)
    const GearMenu = () => (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={() => setShowGearMenu(false)}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl p-6"
                onClick={e => e.stopPropagation()}
            >
                <div className="flex items-center justify-between mb-6">
                    <span className="text-xl font-medium text-gray-800">
                        Управление
                    </span>
                    <button
                        onClick={() => setShowGearMenu(false)}
                        className="text-gray-400 hover:text-gray-600 text-xl"
                    >
                        ✕
                    </button>
                </div>

                <div className="space-y-2">
                    <button
                        onClick={() => {
                            setShowGearMenu(false)
                            navigate(isClub ? `/club/${id}/edit` : `/group/${id}/edit`)
                        }}
                        className="w-full text-left p-4 bg-gray-50 hover:bg-gray-100 rounded-xl flex items-center gap-3 text-gray-700 transition-colors"
                    >
                        <span className="text-xl">✏️</span>
                        <span className="font-medium">Редактировать</span>
                    </button>

                    <button
                        onClick={() => {
                            setShowGearMenu(false)
                            handleDelete()
                        }}
                        className="w-full text-left p-4 bg-red-50 hover:bg-red-100 rounded-xl flex items-center gap-3 text-red-600 transition-colors"
                    >
                        <span className="text-xl">🗑️</span>
                        <span className="font-medium">Удалить {isClub ? 'клуб' : 'группу'}</span>
                    </button>
                </div>
            </div>
        </div>
    )

    // Compact Group Chip component
    const GroupChip = ({ group }) => (
        <button
            onClick={() => navigate(`/group/${group.id}`)}
            className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-left hover:bg-gray-100 transition-colors flex-shrink-0"
        >
            <div className="flex items-center gap-1.5">
                <span className="text-sm text-gray-800 truncate max-w-[120px]">{group.name}</span>
                {group.telegramChatId && <span className="text-green-500 text-xs">✓</span>}
            </div>
            <p className="text-xs text-gray-500">{group.members} чел</p>
        </button>
    )

    // Navigate to Home with filter via URL params
    const handleViewAllActivities = () => {
        const params = new URLSearchParams()
        params.set('mode', 'all')  // Show all activities, not just "my"
        if (isClub) {
            params.set('clubId', id)
            params.set('clubName', item.name)
        } else {
            params.set('groupId', id)
            params.set('groupName', item.name)
        }
        navigate(`/?${params.toString()}`)
    }

    // Navigate to schedule (same as view all for members)
    const handleViewSchedule = () => {
        handleViewAllActivities()
    }

    // Stats placeholder for admin
    const handleViewStats = () => {
        showToast('Статистика пока в разработке')
    }

    return (
        <div className="h-screen bg-white flex flex-col relative">
            {showGearMenu && <GearMenu />}

            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="text-gray-500 text-sm hover:text-gray-700"
                >
                    ← Назад
                </button>

                {isAdmin && (
                    <button
                        onClick={() => setShowGearMenu(true)}
                        className="p-1 text-gray-400 hover:text-gray-600 active:scale-95 transition-all"
                    >
                        <svg
                            className="w-3.5 h-3.5"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth={2.5}
                            strokeLinecap="round"
                        >
                            <line x1="4" y1="4" x2="4" y2="20" />
                            <circle cx="4" cy="14" r="2.5" fill="currentColor" stroke="none" />
                            <line x1="12" y1="4" x2="12" y2="20" />
                            <circle cx="12" cy="8" r="2.5" fill="currentColor" stroke="none" />
                            <line x1="20" y1="4" x2="20" y2="20" />
                            <circle cx="20" cy="16" r="2.5" fill="currentColor" stroke="none" />
                        </svg>
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4 pb-32">
                {/* Main Info Card */}
                <div className="border border-gray-200 rounded-xl p-4 mb-4">
                    {/* Header: info left, avatar right */}
                    <div className="flex items-start justify-between gap-4 mb-4">
                        {/* Left: info */}
                        <div className="flex-1 min-w-0">
                            <h1 className="text-lg text-gray-800 font-medium break-words">
                                {item.name}
                            </h1>

                            {/* Parent club for groups */}
                            {!isClub && (item.club_name || item.parentClub) && item.clubId && (
                                <button
                                    onClick={() => navigate(`/club/${item.clubId}`)}
                                    className="text-sm text-gray-400 mt-0.5 hover:text-gray-600"
                                >
                                    {item.club_name || item.parentClub} →
                                </button>
                            )}

                            {/* Stats line: members, groups, visibility */}
                            <p className="text-sm text-gray-500 mt-2">
                                {pluralizeMembers(item.members)}
                                {isClub && item.groupsCount > 0 && ` · ${pluralizeGroups(item.groupsCount)}`}
                                {' · '}
                                {item.isOpen ? '🌐' : '🔒'}
                            </p>

                            {/* Sports icons */}
                            {item.sports && item.sports.length > 0 && (
                                <div className="flex gap-1 mt-2">
                                    {item.sports.map(sportId => {
                                        const icon = getSportIcon(sportId)
                                        return icon ? (
                                            <span key={sportId} className="text-base">{icon}</span>
                                        ) : null
                                    })}
                                </div>
                            )}
                        </div>

                        {/* Right: avatar with TG badge overlay */}
                        <div className="flex-shrink-0 relative">
                            {item.photo ? (
                                <Avatar src={item.photo} name={item.name} size="xl" forcePhoto />
                            ) : (
                                <span className="text-5xl">{isClub ? '🏆' : '👥'}</span>
                            )}
                            {item.telegramChatId && (
                                <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-[#0088cc] rounded-full flex items-center justify-center shadow-sm">
                                    <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                                    </svg>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Description */}
                    {item.description && (
                        <>
                            <div className="border-t border-gray-200 my-4" />
                            <Linkify className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap break-words block">
                                {item.description}
                            </Linkify>
                        </>
                    )}

                    {/* Activities section */}
                    <div className="border-t border-gray-200 my-4" />
                    {upcomingActivities.length > 0 ? (
                        <div>
                            <div className="flex items-center justify-between mb-3">
                                <p className="text-sm text-gray-500">Ближайшие активности</p>
                                {activities.length > 0 && (
                                    <button
                                        onClick={handleViewAllActivities}
                                        className="text-xs text-gray-400 hover:text-gray-600"
                                    >
                                        Все ({activities.length}) →
                                    </button>
                                )}
                            </div>
                            <div className="space-y-2">
                                {upcomingActivities.slice(0, 3).map(activity => (
                                    <MiniActivityCard key={activity.id} activity={activity} />
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="border border-dashed border-gray-200 rounded-xl p-4 text-center">
                            <span className="text-xl mb-1 block">📅</span>
                            <p className="text-sm text-gray-400 mb-2">Нет запланированных</p>
                            {item.isMember && (
                                <button
                                    onClick={() => setShowCreateMenu(true)}
                                    className="text-sm text-gray-500 hover:text-gray-700"
                                >
                                    {isAdmin ? 'Создать →' : 'Предложить →'}
                                </button>
                            )}
                        </div>
                    )}

                    {/* Groups section (only for clubs) */}
                    {isClub && clubGroups.length > 0 && (
                        <>
                            <div className="border-t border-gray-200 my-4" />
                            <div>
                                <p className="text-sm text-gray-500 mb-3">Группы ({clubGroups.length})</p>
                                <div className="flex flex-wrap gap-2">
                                    {clubGroups.map(group => (
                                        <GroupChip key={group.id} group={group} />
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    {/* Participants section */}
                    <div className="border-t border-gray-200 my-4" />
                    <div>
                        <div className="flex items-center gap-1 mb-3">
                            <p className="text-sm text-gray-500">Участники ({item.members})</p>
                            {item.isMember && (
                                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </div>
                        <button
                            onClick={() => setShowParticipants(true)}
                            className="flex items-center"
                        >
                            <AvatarStack participants={participants} max={5} size="sm" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Participants sheet */}
            <ParticipantsSheet
                isOpen={showParticipants}
                onClose={() => setShowParticipants(false)}
                participants={participants}
                title="Участники"
            />

            {/* Create Menu */}
            <CreateMenu
                isOpen={showCreateMenu}
                onClose={() => setShowCreateMenu(false)}
                context={isClub
                    ? { clubId: item.id, name: item.name }
                    : { groupId: item.id, clubId: item.clubId, name: item.name }}
            />

            {/* Bottom Bar with Action */}
            <BottomBar
                onCreateClick={() => setShowCreateMenu(true)}
                canCreate={item?.canCreateActivity}
                action={
                    !item.isMember ? (
                        <Button
                            onClick={toggleMembership}
                            loading={joiningClub || joiningGroup}
                        >
                            {item.isOpen ? 'Вступить' : '🔒 Отправить заявку'}
                        </Button>
                    ) : isAdmin ? (
                        <div className="flex gap-2">
                            <Button
                                disabled
                                variant="secondary"
                                className="flex-1"
                            >
                                📊 Аналитика <span className="text-xs">(в работе)</span>
                            </Button>
                            <Button
                                onClick={handleViewSchedule}
                                className="flex-1"
                            >
                                📅 Расписание
                            </Button>
                        </div>
                    ) : (
                        <Button onClick={handleViewSchedule}>
                            📅 Расписание
                        </Button>
                    )
                }
            />
        </div>
    )
}
