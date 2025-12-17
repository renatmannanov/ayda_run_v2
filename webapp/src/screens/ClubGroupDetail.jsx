import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CreateMenu, ParticipantsSheet, ActivityCard, GroupCard, LoadingScreen, ErrorScreen, Button, BottomNav } from '../components'
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
import { pluralizeMembers, pluralizeGroups } from '../data/sample_data'

export default function ClubGroupDetail({ type = 'club' }) {
    const { id } = useParams()
    const navigate = useNavigate()

    const isClub = type === 'club'

    // Fetch item data
    // ALWAYS call both hooks to respect React Rules of Hooks
    // Pass null if not applicable (hooks in useApi.js are now guarded)
    const {
        data: clubData,
        loading: clubLoading,
        error: clubError,
        refetch: refetchClub
    } = useClub(isClub ? id : null)

    const {
        data: groupData,
        loading: groupLoading,
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
        loading: activitiesLoading
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

    const upcomingActivities = activities.filter(a => !a.isPast).slice(0, 3)

    const toggleMembership = async () => {
        try {
            if (isClub) {
                await joinClub(id)
            } else {
                await joinGroup(id)
            }
            refetch()
        } catch (e) {
            console.error('Membership toggle failed', e)
        }
    }

    const handleDelete = async () => {
        tg.showConfirm(`Вы действительно хотите удалить этот ${isClub ? 'клуб' : 'группу'}?`, async (confirmed) => {
            if (confirmed) {
                try {
                    if (isClub) await deleteClub(id)
                    else await deleteGroup(id)
                    navigate('/clubs')
                } catch (e) {
                    console.error('Delete failed', e)
                    // TODO: show alert
                }
            }
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

    return (
        <div className="h-screen bg-white flex flex-col relative">
            {showGearMenu && <GearMenu />}

            {/* Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="text-gray-500 text-sm hover:text-gray-700"
                >
                    ← Назад
                </button>

                {isAdmin && (
                    <button
                        onClick={() => setShowGearMenu(true)}
                        className="text-xl p-2 -mr-2 text-gray-500 hover:text-gray-700 active:scale-95 transition-transform"
                    >
                        ⚙️
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4 pb-24">
                {/* Main Info Card */}
                <div className="border border-gray-200 rounded-xl p-4 mb-4">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1 pr-3">
                            <h1 className="text-xl text-gray-800 font-medium mb-1">
                                {item.name}
                                {!isClub && (item.club_name || item.parentClub) && (
                                    <span className="text-gray-400 font-normal"> / {item.club_name || item.parentClub}</span>
                                )}
                            </h1>
                            <p className="text-sm text-gray-500">
                                {isClub ? '🏆 Клуб' : '👥 Группа'}
                            </p>
                        </div>
                        <span className="text-3xl flex-shrink-0">{isClub ? '🏆' : '👥'}</span>
                    </div>

                    {item.description && (
                        <p className="text-sm text-gray-700 leading-relaxed mb-4">
                            {item.description}
                        </p>
                    )}

                    <div className="border-t border-gray-200 pt-4 flex items-center justify-between">
                        <button
                            onClick={() => setShowParticipants(true)}
                            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                        >
                            <div className="flex -space-x-2">
                                {participants.slice(0, 5).map((p, i) => (
                                    <span key={p.id || i} className="text-xl">{p.avatar || '👤'}</span>
                                ))}
                            </div>
                            <span>
                                {pluralizeMembers(item.members)}
                                {isClub && item.groupsCount > 0 && ` · ${pluralizeGroups(item.groupsCount)}`}
                            </span>
                        </button>

                        {/* Inline Join/Member Status - NEW */}
                        {item.isMember ? (
                            <span className="text-sm font-medium text-green-600 bg-green-50 px-3 py-1 rounded-full">
                                Участник ✓
                            </span>
                        ) : (
                            <button
                                onClick={toggleMembership}
                                disabled={joiningClub || joiningGroup}
                                className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full hover:bg-blue-100 transition-colors"
                            >
                                {joiningClub || joiningGroup ? '...' : 'Вступить'}
                            </button>
                        )}
                    </div>
                </div>

                {/* Groups (only for clubs) */}
                {isClub && clubGroups.length > 0 && (
                    <div className="mb-4">
                        <p className="text-sm text-gray-500 mb-3">Группы</p>
                        {clubGroups.map(group => (
                            <GroupCard key={group.id} group={group} />
                        ))}
                    </div>
                )}

                {/* Upcoming Activities */}
                {upcomingActivities.length > 0 ? (
                    <div className="mb-4">
                        <p className="text-sm text-gray-500 mb-3">Ближайшие тренировки</p>
                        {upcomingActivities.map(activity => (
                            <ActivityCard key={activity.id} activity={activity} />
                        ))}
                    </div>
                ) : (
                    <div className="border border-dashed border-gray-200 rounded-xl p-6 text-center mb-4">
                        <span className="text-2xl mb-2 block">📅</span>
                        <p className="text-sm text-gray-400 mb-3">Нет запланированных тренировок</p>
                        <button
                            onClick={() => setShowCreateMenu(true)}
                            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                        >
                            {isAdmin ? 'Создать тренировку →' : 'Предложить тренировку →'}
                        </button>
                    </div>
                )}
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

            {/* Bottom Navigation */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto z-40">
                <BottomNav onCreateClick={() => setShowCreateMenu(true)} />
            </div>
        </div>
    )
}
