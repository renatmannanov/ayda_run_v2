import React from 'react'
import { useNavigate } from 'react-router-dom'
import { formatTime, formatDate } from '../../data/sample_data'

// Status Button Component - контурный круг с иконкой
const StatusButton = ({ status, isPrivate, isPast, attended, isFull }) => {
    // Прошедшая активность - текстовый статус
    if (isPast) {
        return (
            <span className={`text-sm ${attended ? 'text-gray-500' : 'text-gray-400'}`}>
                {attended ? 'Был ✓' : 'Пропустил'}
            </span>
        )
    }

    // Мест нет
    if (isFull) {
        return <span className="text-sm text-gray-400">Мест нет</span>
    }

    // Замочек для закрытых (показывается слева от кнопки)
    const lockIcon = isPrivate && status === 'none' && (
        <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
    )

    // Был на тренировке - зелёная галочка
    if (status === 'attended') {
        return (
            <div className="flex items-center gap-1.5">
                {lockIcon}
                <div className="w-7 h-7 rounded-full border-2 border-green-500 flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
            </div>
        )
    }

    // Записан - серая галочка
    if (status === 'registered') {
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

    // Не записан - плюс
    return (
        <div className="flex items-center gap-1.5">
            {lockIcon}
            <div className="w-7 h-7 rounded-full border-2 border-gray-400 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m6-6H6" />
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
            return parts.join(' · ')
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

    return (
        <div
            onClick={handleCardClick}
            className="bg-white border border-gray-200 rounded-xl p-4 mb-3 cursor-pointer hover:border-gray-300 transition-colors"
        >
            {/* Название + иконка спорта */}
            <div className="flex justify-between items-start mb-1">
                <h3 className="text-base text-gray-800 font-medium pr-2">
                    {activity.title}
                </h3>
                <span className="text-xl flex-shrink-0">{activity.icon}</span>
            </div>

            {/* Организатор */}
            {organizerText && (
                <p className="text-sm text-gray-500 mb-1">{organizerText}</p>
            )}

            {/* Дата, время, место */}
            <p className="text-sm text-gray-500 mb-1">
                {formatDate(activity.date)}, {formatTime(activity.date)} · {activity.location}
            </p>

            {/* Дистанция и набор (если есть) */}
            {distanceText && (
                <p className="text-sm text-gray-400 mb-2">{distanceText}</p>
            )}

            {/* Участники + кнопка статуса */}
            <div className="flex justify-between items-center mt-3">
                <span className="text-sm text-gray-500">
                    {activity.maxParticipants !== null
                        ? `${activity.participants}/${activity.maxParticipants}`
                        : `${activity.participants}`}
                </span>
                <StatusButton
                    status={getStatus()}
                    isPrivate={!activity.isOpen}
                    isPast={activity.isPast}
                    attended={activity.attended}
                    isFull={isFull}
                />
            </div>
        </div>
    )
}
