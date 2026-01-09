import React from 'react'
import { useNavigate } from 'react-router-dom'
import { formatTime, formatDate } from '../../data/sample_data'

// Status Button Component - контурный круг с иконкой
const StatusButton = ({ status, isPrivate, isPast, isFull, participationStatus }) => {
    // Прошедшая активность без записи - часы
    if (isPast && !participationStatus && status === 'none') {
        return (
            <div className="flex items-center gap-1.5">
                <div className="w-7 h-7 rounded-full border-2 border-gray-300 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
                    </svg>
                </div>
            </div>
        )
    }

    // Мест нет (только для будущих активностей без регистрации)
    if (isFull && !participationStatus) {
        return <span className="text-sm text-gray-400">Мест нет</span>
    }

    // Замочек для закрытых (показывается слева от кнопки)
    const lockIcon = isPrivate && status === 'none' && (
        <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
    )

    // Ожидает подтверждения - оранжевый знак вопроса
    if (participationStatus === 'awaiting') {
        return (
            <div className="flex items-center gap-1.5">
                <div className="w-7 h-7 rounded-full border-2 border-orange-400 flex items-center justify-center">
                    <span className="text-orange-400 font-bold text-sm">?</span>
                </div>
            </div>
        )
    }

    // Был на тренировке - зелёная галочка (без opacity, opacity на карточке)
    if (participationStatus === 'attended') {
        return (
            <div className="flex items-center gap-1.5">
                <div className="w-7 h-7 rounded-full border-2 border-green-500 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
            </div>
        )
    }

    // Пропустил - серый крестик (без opacity, opacity на карточке)
    if (participationStatus === 'missed') {
        return (
            <div className="flex items-center gap-1.5">
                <div className="w-7 h-7 rounded-full border-2 border-gray-400 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </div>
            </div>
        )
    }

    // Записан - серая галочка
    if (status === 'registered' || participationStatus === 'registered' || participationStatus === 'confirmed') {
        return (
            <div className="flex items-center gap-1.5">
                {lockIcon}
                <div className="w-7 h-7 rounded-full border-2 border-gray-400 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
            </div>
        )
    }

    // Заявка отправлена (pending) - часы
    if (status === 'pending') {
        return (
            <div className="flex items-center gap-1.5">
                {lockIcon}
                <div className="w-7 h-7 rounded-full border-2 border-gray-400 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
                    </svg>
                </div>
            </div>
        )
    }

    // Не записан - стрелка вправо с палочкой
    return (
        <div className="flex items-center gap-1.5">
            {lockIcon}
            <div className="w-7 h-7 rounded-full border-2 border-gray-400 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
            </div>
        </div>
    )
}

export default function ActivityCard({ activity }) {
    const navigate = useNavigate()
    const isFull = activity.maxParticipants !== null && activity.participants >= activity.maxParticipants

    const handleCardClick = () => {
        navigate(`/activity/${activity.id}`)
    }

    // Получить текст организатора
    const getOrganizerText = () => {
        // Если есть клуб или группа - показываем их
        if (activity.club || activity.group) {
            const parts = [activity.club, activity.group].filter(Boolean)
            return `организатор · ${parts.join(' · ')}`
        }
        // Для личных активностей показываем создателя
        if (activity.creatorName) {
            return `организатор · ${activity.creatorName}`
        }
        return null
    }

    // Получить текст дистанции/набора (скрываем если пустые)
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

    // Определить статус для кнопки
    const getStatus = () => {
        if (activity.attended) return 'attended'
        if (activity.isPending) return 'pending' // TODO: добавить isPending в API
        if (activity.isJoined) return 'registered'
        return 'none'
    }

    const organizerText = getOrganizerText()
    const distanceText = getDistanceText()

    // Opacity для завершённых статусов (attended/missed) и прошедших без записи
    const isConfirmedPast = activity.participationStatus === 'attended' || activity.participationStatus === 'missed'
    const isPastNotJoined = activity.isPast && !activity.isJoined && !activity.participationStatus

    return (
        <div
            onClick={handleCardClick}
            className={`bg-white border border-gray-200 rounded-xl p-4 mb-3 cursor-pointer hover:border-gray-300 transition-colors ${isConfirmedPast || isPastNotJoined ? 'opacity-50' : ''}`}
        >
            {/* Блок 1: Название + организатор */}
            <div className="mb-3">
                <div className="flex justify-between items-start">
                    <div className="flex items-center gap-1.5 pr-2">
                        <h3 className="text-base text-gray-800 font-medium">
                            {activity.title}
                        </h3>
                        {activity.isRecurring && (
                            <span className="flex items-center gap-0.5 text-xs text-gray-400" title="Повторяющаяся тренировка">
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                <span>#{activity.recurringSequence}</span>
                            </span>
                        )}
                    </div>
                    <span className="text-xl flex-shrink-0">{activity.icon}</span>
                </div>
                {organizerText && (
                    <p className="text-sm text-gray-500">{organizerText}</p>
                )}
            </div>

            {/* Блок 2: Дата, время, место + дистанция */}
            <div className="mb-3">
                <p className="text-sm text-gray-500">
                    {formatDate(activity.date)}, {formatTime(activity.date)} · {activity.location}
                </p>
                {distanceText && (
                    <p className="text-sm text-gray-400">{distanceText}</p>
                )}
            </div>

            {/* Блок 3: Участники + кнопка статуса */}
            <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">
                    {activity.maxParticipants !== null
                        ? `${activity.participants}/${activity.maxParticipants} участников`
                        : `${activity.participants} участников`}
                </span>
                <StatusButton
                    status={getStatus()}
                    isPrivate={!activity.isOpen}
                    isPast={activity.isPast}
                    isFull={isFull}
                    participationStatus={activity.participationStatus}
                />
            </div>
        </div>
    )
}
