import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ParticipantsSheet, LoadingScreen, ErrorScreen, Button, BottomNav } from '../components'
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
    const isFull = activity ? activity.participants >= activity.maxParticipants : false
    const isJoined = activity?.isJoined

    // Toggle join
    const handleJoinToggle = async () => {
        try {
            if (isJoined) {
                await leaveActivity(id)
            } else {
                await joinActivity(id)
            }
            // Refetch both to update UI count and list
            refetchActivity()
            refetchParticipants()
        } catch (e) {
            console.error('Action failed', e)
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

                        {activity.gpxLink && (
                            <div className="flex items-start gap-3">
                                <span className="text-gray-400">📎</span>
                                <a
                                    href={activity.gpxLink}
                                    className="text-sm text-gray-700 hover:text-gray-900 underline underline-offset-2"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    Маршрут GPX →
                                </a>
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
                            Участники · {isPast
                                ? `${attendedCount} из ${participants.length} были`
                                : `${activity.participants}/${activity.maxParticipants}`
                            }
                        </p>

                        <button
                            onClick={() => setShowParticipants(true)}
                            className="flex items-center gap-1 w-full text-left"
                            disabled={participantsLoading}
                        >
                            {participantsLoading ? (
                                <span className="text-sm text-gray-400">Загрузка участников...</span>
                            ) : (
                                <>
                                    <div className="flex -space-x-2">
                                        {displayedParticipants.map(p => (
                                            <span
                                                key={p.id}
                                                className={`text-2xl ${isPast && p.attended === false ? 'opacity-40' : ''}`}
                                            >
                                                {p.avatar || '👤'}
                                            </span>
                                        ))}
                                    </div>
                                    {remainingCount > 0 && (
                                        <span className="text-sm text-gray-400 ml-2">
                                            +{remainingCount} →
                                        </span>
                                    )}
                                </>
                            )}
                        </button>

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

                    {/* Organizer actions */}
                    {isOrganizer && (
                        <div className="mt-6 pt-4 border-t border-gray-200">
                            <div className="flex gap-4 mb-4">
                                <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                                    ✏️ Редактировать
                                </button>
                                <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                                    🔗 Поделиться
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
                                Записаться
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
