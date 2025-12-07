import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CreateMenu, ParticipantsSheet, ActivityCard, GroupCard, LoadingScreen, ErrorScreen, Button } from '../components'
import {
    useClub,
    useGroup,
    useActivities,
    useJoinClub,
    useJoinGroup,
    useGroups // To fetch groups for a club
} from '../hooks'
import { pluralizeMembers, pluralizeGroups } from '../data/sample_data'

export default function ClubGroupDetail({ type = 'club' }) {
    const { id } = useParams()
    const navigate = useNavigate()

    const isClub = type === 'club'

    // Fetch item data
    const {
        data: clubData,
        loading: clubLoading,
        error: clubError,
        refetch: refetchClub
    } = isClub ? useClub(id) : { data: null, loading: false }

    const {
        data: groupData,
        loading: groupLoading,
        error: groupError,
        refetch: refetchGroup
    } = !isClub ? useGroup(id) : { data: null, loading: false }

    const item = isClub ? clubData : groupData
    const loading = isClub ? clubLoading : groupLoading
    const error = isClub ? clubError : groupError
    const refetch = isClub ? refetchClub : refetchGroup

    // Fetch groups if it's a club (to show subgroups)
    // Logic: if club, fetch groups passing clubId. API might support this.
    // Assuming useGroups(clubId) works if we implemented it in useApi.js
    // Let's verify usage in useApi.js: export function useGroups(clubId = null) { ... } -> Yes.
    const { data: clubGroups = [] } = isClub ? useGroups(id) : { data: [] }

    // Fetch activities for this club/group
    // useActivities accepts filters { club_id: id } or { group_id: id }
    const filters = isClub ? { club_id: id } : { group_id: id }
    const {
        data: activities = [],
        loading: activitiesLoading
    } = useActivities(filters)

    const { mutate: joinClub, loading: joiningClub } = useJoinClub()
    const { mutate: joinGroup, loading: joiningGroup } = useJoinGroup()

    const [showParticipants, setShowParticipants] = useState(false)
    const [showCreateMenu, setShowCreateMenu] = useState(false)

    // Participants list - usually separate endpoint but often included in light detail or we fetch separately
    // For now assuming 'item' has 'members_list' or similar, OR we use a separate hook if needed.
    // Sample data had 'members' as count, maybe 'participants' array.
    // Let's assume we might need a useClubMembers hook later if list is large.
    // For now, let's use what we have or sample data placeholder if data missing for list view.
    // Actually, let's just show a placeholder or empty list if backend doesn't return list in get().
    const participants = item?.members_list || []
    // NOTE: If backend get() doesn't return members list, we might need useClubMembers(id)

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

    const isAdmin = item?.isAdmin

    if (loading) return <LoadingScreen text={`Загружаем ${isClub ? 'клуб' : 'группу'}...`} />
    if (error) return <ErrorScreen message={error} onRetry={refetch} />
    if (!item) return <ErrorScreen message="Не найдено" />

    return (
        <div className="min-h-screen bg-white flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="text-gray-500 text-sm hover:text-gray-700"
                >
                    ← Назад
                </button>

                {isAdmin && (
                    <button className="text-sm text-gray-500 hover:text-gray-700">
                        ⚙️
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto px-4 py-4">
                {/* Main Info Card */}
                <div className="border border-gray-200 rounded-xl p-4 mb-4">
                    <div className="flex items-start justify-between mb-4">
                        <div className="flex-1 pr-3">
                            <h1 className="text-xl text-gray-800 font-medium mb-1">
                                {item.name}
                                {!isClub && item.parentClub && (
                                    <span className="text-gray-400 font-normal"> / {item.parentClub}</span>
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

                    <div className="border-t border-gray-200 pt-4">
                        <button
                            onClick={() => setShowParticipants(true)}
                            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                        >
                            <div className="flex -space-x-2">
                                {/* Fallback to simple slice if participants field exists, else empty */}
                                {participants.slice(0, 5).map((p, i) => (
                                    <span key={p.id || i} className="text-xl">{p.avatar || '👤'}</span>
                                ))}
                            </div>
                            <span>
                                {pluralizeMembers(item.members)}
                                {isClub && item.groupsCount > 0 && ` · ${pluralizeGroups(item.groupsCount)}`}
                            </span>
                            <span>→</span>
                        </button>
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

                {/* Admin actions */}
                {isAdmin && (
                    <div className="border border-gray-200 rounded-xl p-4 mb-4">
                        <p className="text-sm text-gray-500 mb-3">Управление</p>
                        <div className="space-y-2">
                            <button className="w-full text-left py-2 text-sm text-gray-700 hover:text-gray-900 transition-colors">
                                ✏️ Редактировать
                            </button>
                            <button className="w-full text-left py-2 text-sm text-gray-700 hover:text-gray-900 transition-colors">
                                🔗 Ссылка приглашения
                            </button>
                            <button className="w-full text-left py-2 text-sm text-gray-700 hover:text-gray-900 transition-colors">
                                👥 Управление участниками
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom CTA */}
            <div className="px-4 pb-6 pt-2 border-t border-gray-100">
                {item.isMember ? (
                    <Button
                        onClick={toggleMembership}
                        variant="secondary"
                        loading={joiningClub || joiningGroup}
                    >
                        <span>Участник ✓</span>
                        <span className="text-gray-400">·</span>
                        <span className="text-gray-400 font-normal">Выйти</span>
                    </Button>
                ) : (
                    <Button
                        onClick={toggleMembership}
                        loading={joiningClub || joiningGroup}
                    >
                        {isClub ? 'Вступить в клуб' : 'Вступить в группу'}
                    </Button>
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
                context={isClub ? { clubId: item.id, name: item.name } : { groupId: item.id, name: item.name }}
            />
        </div>
    )
}
