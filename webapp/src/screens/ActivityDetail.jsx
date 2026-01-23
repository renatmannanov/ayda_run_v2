import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ParticipantsSheet, LoadingScreen, ErrorScreen, Button, BottomBar, AttendancePopup } from '../components'
import { AvatarStack, GPXUploadPopup, RecurringScopeDialog, StatusBadge } from '../components/ui'
import {
    useActivity,
    useActivityParticipants,
    useJoinActivity,
    useLeaveActivity,
    useConfirmActivity,
    useDeleteActivity
} from '../hooks'
import { useCancelRecurring } from '../hooks/useRecurring'
import {
    formatDate,
    formatTime,
    getDifficultyLabel
} from '../data/sample_data'
import { activitiesApi, clubsApi, groupsApi, analyticsApi, configApi, tg } from '../api'
import { useToast } from '../contexts/ToastContext'

export default function ActivityDetail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const { showToast } = useToast()

    // Fetch activity
    const {
        data: activity,
        isLoading: activityLoading,
        error: activityError,
        refetch: refetchActivity
    } = useActivity(id)

    // Fetch participants
    const {
        data: participantsData,
        loading: participantsLoading,
        refetch: refetchParticipants
    } = useActivityParticipants(id)

    const participants = participantsData || []

    const { mutate: joinActivity, loading: joining } = useJoinActivity()
    const { mutate: leaveActivity, loading: leaving } = useLeaveActivity()
    const { mutate: confirmActivity, isPending: confirming } = useConfirmActivity()
    const { mutate: deleteActivity, isPending: deleting } = useDeleteActivity()
    const { mutate: cancelRecurring, isPending: cancellingRecurring } = useCancelRecurring()

    const [showParticipants, setShowParticipants] = useState(false)
    const [showGpxPopup, setShowGpxPopup] = useState(false)
    const [showAttendance, setShowAttendance] = useState(false)
    const [attendanceData, setAttendanceData] = useState([])
    const [clubGroupMembers, setClubGroupMembers] = useState([])
    const [savingAttendance, setSavingAttendance] = useState(false)

    // Recurring activity dialog state
    const [showRecurringDialog, setShowRecurringDialog] = useState(false)
    const [recurringDialogMode, setRecurringDialogMode] = useState('edit') // 'edit' | 'cancel'

    // Sync participants to attendance data
    useEffect(() => {
        if (participants.length > 0) {
            setAttendanceData(participants.map(p => ({
                ...p,
                attended: p.attended // null, true, or false
            })))
        }
    }, [participants])

    // Load club/group members when opening attendance popup
    useEffect(() => {
        if (showAttendance && activity) {
            const loadMembers = async () => {
                try {
                    if (activity.clubId) {
                        const members = await clubsApi.getMembers(activity.clubId)
                        setClubGroupMembers(members)
                    } else if (activity.groupId) {
                        const members = await groupsApi.getMembers(activity.groupId)
                        setClubGroupMembers(members)
                    }
                } catch (e) {
                    // Silently fail - members list is optional
                }
            }
            loadMembers()
        }
    }, [showAttendance, activity?.clubId, activity?.groupId])

    // Derived state
    const isPast = activity?.isPast
    const isFull = activity ? (activity.maxParticipants !== null && activity.participants >= activity.maxParticipants) : false
    const isJoined = activity?.isJoined
    const isCreator = activity?.isCreator
    const isPending = activity?.isPending // TODO: add to API

    // Can edit: creator or club/group admin
    const canEdit = isCreator // TODO: add club/group admin check

    // Can mark attendance: organizer + past + club/group activity
    const isClubGroupActivity = activity?.clubId || activity?.groupId
    const canMarkAttendance = isCreator && isPast && isClubGroupActivity

    // Join/Leave handler
    const handleJoin = async () => {
        try {
            // Club members can join directly even for closed activities
            if (activity.isOpen || activity.isClubMember) {
                await joinActivity(id)
                showToast('Записано')
            } else {
                await activitiesApi.requestJoin(id)
                showToast('Заявка отправлена')
            }
            refetchActivity()
            refetchParticipants()
        } catch (e) {
            showToast(e.message || 'Произошла ошибка', 'error')
        }
    }

    const handleLeave = async () => {
        try {
            await leaveActivity(id)
            showToast('Запись отменена', 'info')
            refetchActivity()
            refetchParticipants()
        } catch (e) {
            showToast(e.message || 'Произошла ошибка', 'error')
        }
    }

    const handleShare = async () => {
        // Use Telegram deep link for sharing
        const shareUrl = await configApi.getShareLink('activity', activity.id)
        navigator.clipboard.writeText(shareUrl)
        showToast('Ссылка скопирована', 'info')
    }

    // Confirm attendance handlers
    const handleConfirmAttended = async () => {
        try {
            tg.haptic('medium')
            await confirmActivity({ id, attended: true })
            tg.hapticNotification('success')
            refetchActivity()
        } catch (e) {
            showToast(e.message || 'Произошла ошибка', 'error')
        }
    }

    const handleConfirmMissed = async () => {
        try {
            tg.haptic('light')
            await confirmActivity({ id, attended: false })
            refetchActivity()
        } catch (e) {
            showToast(e.message || 'Произошла ошибка', 'error')
        }
    }

    // Delete activity handler
    const handleDelete = () => {
        if (isPast) {
            showToast('Нельзя удалить прошедшую тренировку', 'error')
            return
        }

        // Wait for participants to load before allowing delete
        if (participantsLoading) {
            showToast('Подождите, загружаем участников...', 'error')
            return
        }

        // For recurring activities, show scope dialog
        if (activity?.isRecurring) {
            setRecurringDialogMode('cancel')
            setShowRecurringDialog(true)
            return
        }

        // Count registered participants (excluding creator)
        // Use String() to ensure correct comparison of UUIDs
        const creatorId = String(activity.creatorId)
        const joinedCount = participants.filter(p =>
            String(p.userId) !== creatorId &&
            ['registered', 'confirmed'].includes(p.status)
        ).length

        const confirmAndDelete = async (notifyParticipants = false) => {
            try {
                tg.haptic('medium')
                await deleteActivity({ id, notifyParticipants })
                tg.hapticNotification('success')
                showToast('Тренировка удалена')
                navigate('/')
            } catch (e) {
                showToast(e.message || 'Ошибка при удалении', 'error')
            }
        }

        if (joinedCount > 0) {
            const word = joinedCount === 1 ? 'участник' :
                        joinedCount < 5 ? 'участника' : 'участников'

            tg.showConfirm(
                `У этой тренировки ${joinedCount} ${word}, которые рассчитывали на неё. Удалить и уведомить их об отмене?`,
                (confirmed) => {
                    if (confirmed) confirmAndDelete(true)
                }
            )
        } else {
            tg.showConfirm(
                'Удалить тренировку?',
                (confirmed) => {
                    if (confirmed) confirmAndDelete(false)
                }
            )
        }
    }

    // Edit activity handler
    const handleEdit = () => {
        if (isPast) {
            showToast('Нельзя редактировать прошедшую тренировку', 'error')
            return
        }
        // For recurring activities, show scope dialog
        if (activity?.isRecurring) {
            setRecurringDialogMode('edit')
            setShowRecurringDialog(true)
            return
        }
        navigate(`/activity/${id}/edit`)
    }

    // Handle recurring scope selection
    const handleRecurringScopeSelect = async (scope) => {
        if (recurringDialogMode === 'edit') {
            // Navigate to edit with scope parameter
            setShowRecurringDialog(false)
            navigate(`/activity/${id}/edit?scope=${scope}`)
        } else {
            // Cancel recurring activity
            try {
                tg.haptic('medium')
                await cancelRecurring({ activityId: id, scope })
                tg.hapticNotification('success')
                setShowRecurringDialog(false)
                if (scope === 'entire_series') {
                    showToast('Вся серия тренировок отменена')
                } else {
                    showToast('Тренировка отменена')
                }
                navigate('/')
            } catch (e) {
                showToast(e.message || 'Ошибка при отмене', 'error')
            }
        }
    }

    // Attendance handlers
    const handleToggleAttendance = (userId) => {
        setAttendanceData(prev => prev.map(p => {
            if ((p.userId || p.id) === userId) {
                // Cycle: null -> true -> false -> null
                let newAttended
                if (p.attended === null || p.attended === undefined) {
                    newAttended = true
                } else if (p.attended === true) {
                    newAttended = false
                } else {
                    newAttended = null
                }
                return { ...p, attended: newAttended }
            }
            return p
        }))
    }

    const handleToggleAll = () => {
        setAttendanceData(prev => {
            const allAttended = prev.every(p => p.attended === true)
            // If all attended -> reset to null, otherwise -> mark all as attended
            const newValue = allAttended ? null : true
            return prev.map(p => ({ ...p, attended: newValue }))
        })
    }

    const handleAddParticipant = async (member) => {
        try {
            // Add to API
            await activitiesApi.addParticipant(id, member.userId || member.id, true)
            // Add to local state
            setAttendanceData(prev => [...prev, {
                ...member,
                attended: true
            }])
            tg.hapticNotification('success')
            refetchParticipants()
        } catch (e) {
            showToast(e.message || 'Не удалось добавить участника', 'error')
        }
    }

    const handleSaveAttendance = async () => {
        setSavingAttendance(true)
        try {
            const participantsToUpdate = attendanceData.map(p => ({
                user_id: p.userId || p.id,
                attended: p.attended
            }))
            await activitiesApi.markAttendance(id, participantsToUpdate)
            tg.hapticNotification('success')
            refetchParticipants()
            setShowAttendance(false)
        } catch (e) {
            showToast(e.message || 'Не удалось сохранить', 'error')
        } finally {
            setSavingAttendance(false)
        }
    }

    // Get action button content (used in both bottom bar and popup)
    const getActionButton = () => {
        // ORGANIZER: Show attendance marking button for past club/group activities
        // This check comes FIRST - organizer always sees check-in button for club/group activities
        if (canMarkAttendance) {
            const markedCount = attendanceData.filter(p => p.attended === true).length
            return (
                <button
                    onClick={() => setShowAttendance(true)}
                    className="w-full h-12 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
                >
                    <span>📋</span>
                    <span>Отметить посещение</span>
                    {attendanceData.length > 0 && (
                        <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                            {markedCount}/{attendanceData.length}
                        </span>
                    )}
                </button>
            )
        }

        // For club/group activities: participants should NOT see self-confirmation buttons
        // Only organizer (handled above) can mark attendance for club/group activities
        // Self-confirmation is only for PERSONAL activities
        const isPersonalActivity = !activity?.clubId && !activity?.groupId

        // Awaiting confirmation - show two buttons (ONLY for personal activities)
        if (isPersonalActivity && activity?.participationStatus === 'awaiting') {
            return (
                <div className="flex items-center gap-3 h-12">
                    <button
                        onClick={handleConfirmMissed}
                        disabled={confirming}
                        className="flex-1 h-full border border-gray-300 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                        Пропустил
                    </button>
                    <button
                        onClick={handleConfirmAttended}
                        disabled={confirming}
                        className="flex-1 h-full bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors disabled:opacity-50"
                    >
                        Участвовал
                    </button>
                </div>
            )
        }

        // Awaiting confirmation for club/group activities - show waiting message
        if (!isPersonalActivity && activity?.participationStatus === 'awaiting') {
            return <StatusBadge variant="awaitingOrganizer" />
        }

        // Attended - show green status (for all activity types)
        if (activity?.participationStatus === 'attended') {
            return <StatusBadge variant="attended" />
        }

        // Missed - show gray status (for all activity types)
        if (activity?.participationStatus === 'missed') {
            return <StatusBadge variant="missed" />
        }

        // Past activity without registration
        if (isPast) {
            return <StatusBadge variant="finished" />
        }

        // Private & not joined & not pending & NOT club member
        // Club members see "Записаться" button instead of "Подать заявку"
        if (!activity?.isOpen && !activity?.isClubMember && !isJoined && !isPending) {
            return (
                <button
                    onClick={handleJoin}
                    disabled={joining || isFull}
                    className="w-full h-12 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2 disabled:bg-gray-300"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span>Подать заявку на участие</span>
                </button>
            )
        }

        // Private & pending (only for non-club-members who sent a request)
        if (!activity?.isOpen && !activity?.isClubMember && isPending) {
            return (
                <div className="flex items-center justify-between h-12">
                    <button
                        onClick={handleLeave}
                        disabled={leaving}
                        className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        Отменить
                    </button>
                    <div className="flex items-center gap-2 text-gray-800">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        <span className="text-sm font-medium">Заявка отправлена</span>
                    </div>
                </div>
            )
        }

        // Open OR club member & not joined
        if ((activity?.isOpen || activity?.isClubMember) && !isJoined) {
            if (isFull) {
                return <StatusBadge variant="noSeats" />
            }
            return (
                <Button
                    onClick={handleJoin}
                    loading={joining}
                    className="w-full h-12"
                >
                    Записаться
                </Button>
            )
        }

        // Joined (open or private)
        if (isJoined) {
            // Creator sees "Invite participants" instead of cancel button
            if (isCreator) {
                return (
                    <div className="flex items-center justify-between h-12">
                        <span className="text-sm text-gray-500">Пригласи участников</span>
                        <button
                            onClick={handleShare}
                            className="w-10 h-10 border border-gray-200 rounded-xl flex items-center justify-center text-gray-500 hover:bg-gray-50 transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                            </svg>
                        </button>
                    </div>
                )
            }

            // Regular participant sees: Cancel | Status | Invite
            // h-12 = 48px = unified height for all action bar elements
            return (
                <div className="flex items-center justify-between h-12">
                    <button
                        onClick={handleLeave}
                        disabled={leaving}
                        className="flex items-center gap-1 text-sm text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <span>&#x2715;</span>
                        <span>{leaving ? 'Отмена...' : 'Отменить'}</span>
                    </button>

                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 rounded-full">
                        <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-sm text-green-600 font-medium">Иду</span>
                    </span>

                    <button
                        onClick={handleShare}
                        className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                    >
                        <span>Позвать друзей</span>
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                        </svg>
                    </button>
                </div>
            )
        }

        return null
    }

    // Count attended
    const attendedCount = participants.filter(p => p.attended === true).length

    if (activityLoading) return <LoadingScreen text="Загружаем детали..." />
    if (activityError) return <ErrorScreen message={activityError} onRetry={refetchActivity} />
    if (!activity) return <ErrorScreen message="Тренировка не найдена" />

    // Get organizer display text
    const getOrganizerDisplay = () => {
        // Club and/or group
        if (activity.club && activity.group) {
            return (
                <p className="text-sm text-gray-700">
                    <span className="cursor-pointer hover:underline">🏆 {activity.club}</span>
                    <span className="text-gray-400"> / </span>
                    <span className="cursor-pointer hover:underline">{activity.group}</span>
                </p>
            )
        }
        if (activity.club) {
            return (
                <p className="text-sm text-gray-700">
                    <span className="cursor-pointer hover:underline">🏆 {activity.club}</span>
                </p>
            )
        }
        if (activity.group) {
            return (
                <p className="text-sm text-gray-700">
                    <span className="cursor-pointer hover:underline">{activity.group}</span>
                </p>
            )
        }
        // Personal activity - show creator
        if (activity.creatorName) {
            return (
                <p className="text-sm text-gray-700 flex items-center gap-1">
                    <span className="text-gray-400">организатор</span>
                    <span className="cursor-pointer hover:underline">{activity.creatorName}</span>
                </p>
            )
        }
        return null
    }

    // Get distance/elevation text (hide if empty)
    const getDistanceText = () => {
        const parts = []
        if (activity.distance) parts.push(`${activity.distance} км`)
        if (activity.elevation) parts.push(`↗${activity.elevation} м`)
        if (activity.duration) {
            const hours = Math.floor(activity.duration / 60)
            const mins = activity.duration % 60
            if (hours > 0 && mins > 0) {
                parts.push(`${hours}ч ${mins}мин`)
            } else if (hours > 0) {
                parts.push(`${hours}ч`)
            } else {
                parts.push(`${mins}мин`)
            }
        }
        return parts.length > 0 ? parts.join(' · ') : null
    }

    const distanceText = getDistanceText()

    return (
        <div className="h-screen bg-white flex flex-col relative">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="text-gray-500 text-sm hover:text-gray-700"
                >
                    ← Назад
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4 pb-32">
                <div className="border border-gray-200 rounded-xl p-4">
                    {/* Title + Icon */}
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h1 className="text-xl text-gray-800 font-medium">
                                    {activity.title}
                                </h1>
                                {activity.isRecurring && (
                                    <span className="flex items-center gap-0.5 text-sm text-gray-400" title="Повторяющаяся тренировка">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                        <span>#{activity.recurringSequence}</span>
                                    </span>
                                )}
                            </div>
                            {isPast && (
                                <span className="text-sm text-gray-400">
                                    Прошла · {formatDate(activity.date)}
                                </span>
                            )}
                        </div>
                        <span className="text-3xl">{activity.icon || '🏃'}</span>
                    </div>

                    {/* Characteristics */}
                    <div className="space-y-2 mb-2">
                        <div className="flex items-center gap-3">
                            <span className="text-base">📅</span>
                            <span className="text-sm text-gray-700">
                                {formatDate(activity.date)}, {formatTime(activity.date)}
                            </span>
                        </div>

                        {/* Difficulty and Duration */}
                        <div className="flex items-center gap-3">
                            <span className="text-base">💪</span>
                            <span className="text-sm text-gray-700">
                                {getDifficultyLabel(activity.difficulty)}
                                {activity.duration && ` · ${activity.duration} мин`}
                            </span>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="text-base">📍</span>
                            <span className="text-sm text-gray-700 break-all">
                                {activity.location}
                            </span>
                        </div>

                        {distanceText && (
                            <div className="flex items-center gap-3">
                                <span className="text-base">🏃</span>
                                <span className="text-sm text-gray-700">{distanceText}</span>
                            </div>
                        )}
                    </div>

                    {/* GPX Download Link */}
                    {activity.hasGpx && activity.canDownloadGpx && (
                        <div className="mt-3 mb-2">
                            <button
                                onClick={async () => {
                                    try {
                                        // Track GPX download
                                        analyticsApi.trackEvent('gpx_download', { activity_id: activity.id }).catch(() => {})
                                        await activitiesApi.downloadGpx(activity.id, activity.gpxFilename)
                                        showToast('GPX файл скачан')
                                    } catch (e) {
                                        showToast(e.message || 'Не удалось скачать GPX', 'error')
                                    }
                                }}
                                className="text-xs text-gray-500 underline hover:text-gray-700 transition-colors"
                            >
                                Скачать gpx трек
                            </button>
                        </div>
                    )}

                    <div className="border-t border-gray-200 my-4" />

                    {/* Description */}
                    {activity.description && (
                        <>
                            <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap break-words">
                                {activity.description}
                            </p>
                            <div className="border-t border-gray-200 my-4" />
                        </>
                    )}

                    {/* Organizer */}
                    <div className="mb-3">
                        {getOrganizerDisplay()}
                    </div>

                    {/* Participants */}
                    <div className="border-t border-gray-200 my-4" />
                    <div>
                        <div className="flex items-center gap-1 mb-3">
                            <p className="text-sm text-gray-500">
                                Участники ({activity.maxParticipants !== null
                                    ? `${activity.participants}/${activity.maxParticipants}`
                                    : activity.participants
                                })
                            </p>
                            {isJoined && (
                                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </div>
                        <button
                            onClick={() => setShowParticipants(true)}
                            className="flex items-center hover:opacity-70 transition-opacity"
                            disabled={participantsLoading || !activity.canViewParticipants}
                        >
                            {activity.canViewParticipants ? (
                                participantsLoading ? (
                                    <span className="text-sm text-gray-400">Загрузка...</span>
                                ) : (
                                    <AvatarStack participants={participants} max={5} size="sm" />
                                )
                            ) : (
                                <span className="text-sm text-gray-400">
                                    🔒 Список скрыт
                                </span>
                            )}
                        </button>
                    </div>

                    {/* User attendance status (past activities) */}
                    {activity.participationStatus === 'awaiting' && (
                        <p className="text-sm mt-3 text-orange-500">
                            Ожидает подтверждения
                        </p>
                    )}
                    {activity.participationStatus === 'attended' && (
                        <p className="text-sm mt-3 text-green-600">
                            Ты был ✓
                        </p>
                    )}
                    {activity.participationStatus === 'missed' && (
                        <p className="text-sm mt-3 text-gray-400">
                            Ты пропустил
                        </p>
                    )}

                    {/* Creator/Admin actions - moved to bottom */}
                    {canEdit && (
                        <>
                            <div className="border-t border-gray-200 my-4" />
                            <div className="space-y-2">
                                {/* Hide GPX button for yoga and workout */}
                                {!['yoga', 'workout'].includes(activity.sportType) && (
                                    !activity.hasGpx ? (
                                        <button
                                            onClick={() => setShowGpxPopup(true)}
                                            className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 py-1 transition-colors"
                                        >
                                            <span className="w-5 text-center">📍</span>
                                            <span className="font-medium">Добавить маршрут</span>
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => setShowGpxPopup(true)}
                                            className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 py-1 transition-colors"
                                        >
                                            <span className="w-5 text-center">📍</span>
                                            <span>{activity.gpxFilename || 'track.gpx'}</span>
                                            <span className="text-gray-400 text-xs">✎</span>
                                        </button>
                                    )
                                )}
                                <button
                                    onClick={handleEdit}
                                    disabled={isPast}
                                    className={`flex items-center gap-2 text-sm py-1 transition-colors ${
                                        isPast
                                            ? 'text-gray-300 cursor-not-allowed opacity-80'
                                            : 'text-gray-500 hover:text-gray-700'
                                    }`}
                                >
                                    <span className="w-5 text-center">✏️</span>
                                    <span>Редактировать</span>
                                </button>
                                <button
                                    onClick={handleDelete}
                                    disabled={isPast || deleting}
                                    className={`flex items-center gap-2 text-sm py-1 transition-colors ${
                                        isPast
                                            ? 'text-gray-300 cursor-not-allowed opacity-80'
                                            : 'text-gray-500 hover:text-red-600'
                                    }`}
                                >
                                    <span className="w-5 text-center">🗑</span>
                                    <span>{deleting ? 'Удаление...' : 'Удалить'}</span>
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Participants sheet with action button */}
            <ParticipantsSheet
                isOpen={showParticipants}
                onClose={() => setShowParticipants(false)}
                participants={participants}
                maxParticipants={activity.maxParticipants}
                isPast={isPast}
                attendedCount={attendedCount}
                actionButton={getActionButton()}
            />

            {/* Bottom Bar with Action */}
            {/* Show action bar when:
                - Future activity (not past)
                - OR organizer can mark attendance (past + club/group + creator)
                - OR personal activity with awaiting status (participant can self-confirm)
                - OR past activity with attended/missed status (show status)
            */}
            <BottomBar
                onCreateClick={() => showToast('Перейдите на Главную для создания')}
                showAction={(
                    !isPast ||
                    canMarkAttendance ||
                    ((!activity?.clubId && !activity?.groupId) && activity?.participationStatus === 'awaiting') ||
                    activity?.participationStatus === 'attended' ||
                    activity?.participationStatus === 'missed' ||
                    (isPast && !activity?.isJoined) // Show "Активность завершена" for past activities without registration
                ) && !showParticipants && !showAttendance}
                action={getActionButton()}
            />

            {/* GPX Upload Popup */}
            <GPXUploadPopup
                isOpen={showGpxPopup}
                onClose={() => setShowGpxPopup(false)}
                onUpload={() => {
                    setShowGpxPopup(false)
                    refetchActivity()
                }}
                mode={activity?.hasGpx ? 'edit' : 'add'}
                existingFile={activity?.hasGpx ? { name: activity.gpxFilename || 'track.gpx' } : null}
                activityId={activity?.id}
            />

            {/* Attendance Popup (for organizers) */}
            <AttendancePopup
                isOpen={showAttendance}
                onClose={() => setShowAttendance(false)}
                participants={attendanceData}
                clubMembers={clubGroupMembers}
                onToggleAttendance={handleToggleAttendance}
                onToggleAll={handleToggleAll}
                onAddParticipant={handleAddParticipant}
                onSave={handleSaveAttendance}
                saving={savingAttendance}
            />

            {/* Recurring Scope Dialog (for edit/cancel) */}
            <RecurringScopeDialog
                isOpen={showRecurringDialog}
                onClose={() => setShowRecurringDialog(false)}
                onSelect={handleRecurringScopeSelect}
                mode={recurringDialogMode}
                loading={cancellingRecurring}
            />
        </div>
    )
}
