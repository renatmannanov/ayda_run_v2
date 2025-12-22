import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ParticipantsSheet, LoadingScreen, ErrorScreen, Button, BottomNav } from '../components'
import { AvatarStack, GpxUpload } from '../components/ui'
import {
    useActivity,
    useActivityParticipants,
    useJoinActivity,
    useLeaveActivity
} from '../hooks'
import {
    formatDate,
    formatTime,
    getDifficultyLabel
} from '../data/sample_data' // Ensure these helpers are exported or move to utils
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
    const [isOrganizer, setIsOrganizer] = useState(false) // TODO: Check from user API vs activity.organizer_id

    // Derived state
    const isPast = activity?.isPast
    const isFull = activity ? (activity.maxParticipants !== null && activity.participants >= activity.maxParticipants) : false
    const isJoined = activity?.isJoined

    // Toggle join
    const handleJoinToggle = async () => {
        try {
            if (isJoined) {
                await leaveActivity(id)
            } else {
                if (activity.isOpen) {
                    // Open activity - join directly
                    await joinActivity(id)
                } else {
                    // Closed activity - send join request
                    await activitiesApi.requestJoin(id)
                    tg.showAlert('Заявка отправлена! Мы уведомим тебя, когда организатор рассмотрит её.')
                }
            }
            // Refetch both to update UI count and list
            refetchActivity()
            refetchParticipants()
        } catch (e) {
            console.error('Action failed', e)
            const errorMessage = e.message || 'Произошла ошибка'
            tg.showAlert(errorMessage)
        }
    }

    // Count attended (backend might provide this field on participant object)
    const attendedCount = participants.filter(p => p.attended === true).length
    const displayedParticipants = participants.slice(0, 5)
    const remainingCount = participants.length - 5

    if (activityLoading) return <LoadingScreen text="Загружаем детали..." />
    if (activityError) return <ErrorScreen message={activityError} onRetry={refetchActivity} />
    if (!activity) return <ErrorScreen message="Тренировка не найдена" />

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

                {/* Demo toggle for organizer mode - remove in prod or link to real permission */}
                <button
                    onClick={() => setIsOrganizer(!isOrganizer)}
                    className={`text-xs px-2 py-1 rounded ${isOrganizer ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500'}`}
                >
                    {isOrganizer ? 'Орг ✓' : 'Орг'}
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-4 pb-36">
                <div className="border border-gray-200 rounded-xl p-4">
                    {/* Title */}
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h1 className="text-xl text-gray-800 font-medium mb-1 flex items-center gap-2">
                                {!activity.isOpen && <span className="text-gray-400 text-lg">🔒</span>}
                                <span>{activity.title}</span>
                            </h1>
                            {isPast && (
                                <span className="text-sm text-gray-400">
                                    Прошла · {formatDate(activity.date)}
                                </span>
                            )}
                        </div>
                        <span className="text-3xl">{activity.icon || '🏃'}</span>
                    </div>

                    {/* Info */}
                    <div className="space-y-3 mb-4">
                        <div className="flex items-start gap-3">
                            <span className="text-gray-400">📅</span>
                            <span className="text-sm text-gray-700">
                                {formatDate(activity.date)}, {formatTime(activity.date)}
                            </span>
                        </div>

                        <div className="flex items-start gap-3">
                            <span className="text-gray-400">📍</span>
                            <span className="text-sm text-gray-700">
                                {activity.location}
                            </span>
                        </div>

                        <div className="flex items-start gap-3">
                            <span className="text-gray-400">🏃</span>
                            <span className="text-sm text-gray-700">
                                {activity.distance} км · ↗{activity.elevation} м · {activity.duration}
                            </span>
                        </div>

                        <div className="flex items-start gap-3">
                            <span className="text-gray-400">⚡</span>
                            <span className="text-sm text-gray-700">
                                {getDifficultyLabel(activity.difficulty)}
                            </span>
                        </div>

                        {/* GPX download link (for users with permission) */}
                        {activity.hasGpx && activity.canDownloadGpx && (
                            <div className="flex items-start gap-3">
                                <span className="text-gray-400">📍</span>
                                <button
                                    onClick={() => {
                                        const url = activitiesApi.getGpxDownloadUrl(activity.id)
                                        // In Telegram WebApp, use openLink to handle downloads
                                        if (tg.webApp?.openLink) {
                                            // openLink opens in external browser which handles downloads
                                            tg.webApp.openLink(window.location.origin + url)
                                        } else {
                                            // Fallback for desktop/browser
                                            window.open(url, '_blank')
                                        }
                                    }}
                                    className="text-sm text-blue-600 hover:text-blue-800 underline underline-offset-2 text-left"
                                >
                                    Download GPX: {activity.gpxFilename || 'route.gpx'}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Divider */}
                    <div className="border-t border-gray-300 my-4" />

                    {/* Description */}
                    {activity.description && (
                        <>
                            <p className="text-sm text-gray-700 leading-relaxed mb-4">
                                {activity.description}
                            </p>
                            <div className="border-t border-gray-300 my-4" />
                        </>
                    )}

                    {/* Participants */}
                    <div className="mb-4">
                        <p className="text-sm text-gray-500 mb-3">
                            Участники · {activity.canViewParticipants
                                ? (isPast
                                    ? `${attendedCount} из ${participants.length} были`
                                    : activity.maxParticipants !== null
                                        ? `${activity.participants}/${activity.maxParticipants}`
                                        : `${activity.participants}`
                                )
                                : `${activity.participants}`
                            }
                            {!activity.canViewParticipants && (
                                <span className="text-xs text-gray-400"> (только участники)</span>
                            )}
                        </p>

                        {activity.canViewParticipants ? (
                            <button
                                onClick={() => setShowParticipants(true)}
                                className="flex items-center gap-2 w-full text-left"
                                disabled={participantsLoading}
                            >
                                {participantsLoading ? (
                                    <span className="text-sm text-gray-400">Загрузка участников...</span>
                                ) : (
                                    <AvatarStack participants={participants} max={5} size="sm" />
                                )}
                            </button>
                        ) : (
                            <p className="text-sm text-gray-400">
                                🔒 Список участников доступен только членам активности
                            </p>
                        )}

                        {/* User attendance status (past activities) */}
                        {isPast && isJoined && (
                            <p className={`text-sm mt-3 ${activity.attended ? 'text-green-600' : 'text-gray-400'
                                }`}>
                                {activity.attended ? 'Ты был ✓' : 'Ты пропустил'}
                            </p>
                        )}
                    </div>

                    {/* Club/Group */}
                    {(activity.club || activity.group) && (
                        <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                            {activity.club}{activity.group ? ` / ${activity.group}` : ''} →
                        </button>
                    )}

                    {/* Creator actions: GPX upload */}
                    {activity.isCreator && (
                        <div className="mt-6 pt-4 border-t border-gray-200">
                            <GpxUpload
                                activityId={activity.id}
                                hasGpx={activity.hasGpx}
                                gpxFilename={activity.gpxFilename}
                                onSuccess={refetchActivity}
                            />
                        </div>
                    )}

                    {/* Organizer actions */}
                    {isOrganizer && (
                        <div className="mt-6 pt-4 border-t border-gray-200">
                            <div className="flex gap-4 mb-4">
                                <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                                    Edit
                                </button>
                                <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                                    Share
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom CTA */}
            {!isPast && (
                <div className="fixed bottom-20 left-0 right-0 max-w-md mx-auto px-4 pb-2 pt-2 z-30 pointer-events-none">
                    <div className="pointer-events-auto shadow-lg rounded-xl overflow-hidden bg-white">
                        {isJoined ? (
                            <Button
                                onClick={handleJoinToggle}
                                variant="success"
                                loading={joining || leaving}
                                className="w-full rounded-none h-12"
                            >
                                <span>Иду ✓</span>
                                <span className="text-green-400">·</span>
                                <span className="text-green-500 font-normal">Отменить</span>
                            </Button>
                        ) : isFull ? (
                            <Button disabled variant="secondary" className="w-full rounded-none h-12">Мест нет</Button>
                        ) : (
                            <Button
                                onClick={handleJoinToggle}
                                loading={joining || leaving}
                                className="w-full rounded-none h-12"
                            >
                                {activity.isOpen ? 'Записаться' : 'Отправить заявку'}
                            </Button>
                        )}
                    </div>
                </div>
            )}

            {/* Participants sheet */}
            <ParticipantsSheet
                isOpen={showParticipants}
                onClose={() => setShowParticipants(false)}
                participants={participants}
                maxParticipants={activity.maxParticipants}
                isPast={isPast}
                attendedCount={attendedCount}
            />

            {/* Bottom Navigation */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto z-40">
                <BottomNav onCreateClick={() => window.alert('Создание из деталей активности пока не поддерживается, перейдите на Главную')} />
            </div>
        </div>
    )
}
