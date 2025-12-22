import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ParticipantsSheet, LoadingScreen, ErrorScreen, Button, BottomBar } from '../components'
import { AvatarStack, GpxUpload } from '../components/ui'
import {
    useActivity,
    useActivityParticipants,
    useJoinActivity,
    useLeaveActivity
} from '../hooks'
import {
    formatDate,
    formatTime
} from '../data/sample_data'
import { activitiesApi, tg } from '../api'

export default function ActivityDetail() {
    const { id } = useParams()
    const navigate = useNavigate()

    // Fetch activity
    const {
        data: activity,
        loading: activityLoading,
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

    const [showParticipants, setShowParticipants] = useState(false)

    // Derived state
    const isPast = activity?.isPast
    const isFull = activity ? (activity.maxParticipants !== null && activity.participants >= activity.maxParticipants) : false
    const isJoined = activity?.isJoined
    const isCreator = activity?.isCreator
    const isPending = activity?.isPending // TODO: add to API

    // Can edit: creator or club/group admin
    const canEdit = isCreator // TODO: add club/group admin check

    // Join/Leave handler
    const handleJoin = async () => {
        try {
            if (activity.isOpen) {
                await joinActivity(id)
            } else {
                await activitiesApi.requestJoin(id)
                tg.showAlert('Заявка отправлена! Мы уведомим тебя, когда организатор рассмотрит её.')
            }
            refetchActivity()
            refetchParticipants()
        } catch (e) {
            console.error('Join failed', e)
            tg.showAlert(e.message || 'Произошла ошибка')
        }
    }

    const handleLeave = async () => {
        try {
            await leaveActivity(id)
            refetchActivity()
            refetchParticipants()
        } catch (e) {
            console.error('Leave failed', e)
            tg.showAlert(e.message || 'Произошла ошибка')
        }
    }

    const handleShare = () => {
        const shareUrl = `https://t.me/aydarun_bot?start=activity_${activity.id}`
        navigator.clipboard.writeText(shareUrl)
        tg.showAlert('Ссылка скопирована!')
    }

    // Get action button content (used in both bottom bar and popup)
    const getActionButton = () => {
        if (isPast) return null

        // Private & not joined & not pending
        if (!activity?.isOpen && !isJoined && !isPending) {
            return (
                <button
                    onClick={handleJoin}
                    disabled={joining || isFull}
                    className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2 disabled:bg-gray-300"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span>Подать заявку на участие</span>
                </button>
            )
        }

        // Private & pending
        if (!activity?.isOpen && isPending) {
            return (
                <div className="flex items-center justify-between">
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

        // Open & not joined
        if (activity?.isOpen && !isJoined) {
            if (isFull) {
                return (
                    <Button disabled variant="secondary" className="w-full h-12">
                        Мест нет
                    </Button>
                )
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
            return (
                <div className="flex items-center justify-between">
                    <button
                        onClick={handleLeave}
                        disabled={leaving}
                        className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        {leaving ? 'Отмена...' : 'Отменить'}
                    </button>
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-800 font-medium">Иду!</span>
                        <button
                            onClick={handleShare}
                            className="w-10 h-10 border border-gray-200 rounded-xl flex items-center justify-center text-gray-500 hover:bg-gray-50 transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                            </svg>
                        </button>
                    </div>
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
            <div className="flex-1 overflow-y-auto px-4 py-4 pb-40">
                <div className="border border-gray-200 rounded-xl p-4">
                    {/* Title + Icon */}
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h1 className="text-xl text-gray-800 font-medium mb-1">
                                {activity.title}
                            </h1>
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

                        <div className="flex items-center gap-3">
                            <span className="text-base">📍</span>
                            <span className="text-sm text-gray-700">
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
                                onClick={() => {
                                    const url = activitiesApi.getGpxDownloadUrl(activity.id)
                                    if (tg.webApp?.openLink) {
                                        tg.webApp.openLink(window.location.origin + url)
                                    } else {
                                        window.open(url, '_blank')
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
                            <p className="text-sm text-gray-600 leading-relaxed">
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
                    <button
                        onClick={() => setShowParticipants(true)}
                        className="flex items-center gap-2 hover:opacity-70 transition-opacity"
                        disabled={participantsLoading || !activity.canViewParticipants}
                    >
                        {activity.canViewParticipants ? (
                            <>
                                {participantsLoading ? (
                                    <span className="text-sm text-gray-400">Загрузка...</span>
                                ) : (
                                    <>
                                        <AvatarStack participants={participants} max={8} size="sm" />
                                        <span className="text-sm text-gray-500 ml-2">
                                            {activity.maxParticipants !== null
                                                ? `${activity.participants}/${activity.maxParticipants}`
                                                : `${activity.participants}`
                                            }
                                        </span>
                                    </>
                                )}
                            </>
                        ) : (
                            <span className="text-sm text-gray-400">
                                🔒 {activity.participants} участников
                            </span>
                        )}
                    </button>

                    {/* User attendance status (past activities) */}
                    {isPast && isJoined && (
                        <p className={`text-sm mt-3 ${activity.attended ? 'text-green-600' : 'text-gray-400'}`}>
                            {activity.attended ? 'Ты был ✓' : 'Ты пропустил'}
                        </p>
                    )}

                    {/* Creator/Admin actions - moved to bottom */}
                    {canEdit && (
                        <>
                            <div className="border-t border-gray-200 my-4" />
                            <div className="space-y-2">
                                {!activity.hasGpx && (
                                    <GpxUpload
                                        activityId={activity.id}
                                        hasGpx={activity.hasGpx}
                                        gpxFilename={activity.gpxFilename}
                                        onSuccess={refetchActivity}
                                    />
                                )}
                                {activity.hasGpx && (
                                    <div className="flex items-center gap-2 text-sm text-gray-500 py-1">
                                        <span>📍</span>
                                        <span>GPX добавлен</span>
                                    </div>
                                )}
                                <button className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors py-1">
                                    <span>✏️</span>
                                    <span>Редактировать</span>
                                </button>
                                <button className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors py-1">
                                    <span>🗑</span>
                                    <span>Удалить</span>
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
            <BottomBar
                onCreateClick={() => tg.showAlert('Создание из деталей активности пока не поддерживается, перейдите на Главную')}
                showAction={!isPast && !showParticipants}
                action={getActionButton()}
            />
        </div>
    )
}
