import React from 'react'
import { useNavigate } from 'react-router-dom'
import { formatTime, formatDate } from '../../data/sample_data'

// Mini Status Icon - компактная версия для маленьких карточек
const MiniStatusIcon = ({ status, isCompleted, participationStatus }) => {
    const iconClass = "w-5 h-5 rounded-full border-2 flex items-center justify-center"
    const svgClass = "w-2.5 h-2.5"

    // Был на тренировке - зелёная галочка
    if (participationStatus === 'attended') {
        return (
            <div className={`${iconClass} border-green-500`}>
                <svg className={`${svgClass} text-green-500`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            </div>
        )
    }

    // Пропустил - серый крестик
    if (participationStatus === 'missed') {
        return (
            <div className={`${iconClass} border-gray-400`}>
                <svg className={`${svgClass} text-gray-400`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </div>
        )
    }

    // Ожидает подтверждения - оранжевый ?
    if (participationStatus === 'awaiting') {
        return (
            <div className={`${iconClass} border-orange-400`}>
                <span className="text-orange-400 font-bold text-xs">?</span>
            </div>
        )
    }

    // Записан - серая галочка
    if (status === 'registered' || participationStatus === 'registered' || participationStatus === 'confirmed') {
        return (
            <div className={`${iconClass} border-gray-400`}>
                <svg className={`${svgClass} text-gray-400`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            </div>
        )
    }

    // Завершённая активность без записи - часы (без внешнего круга, т.к. часы уже круглые)
    if (isCompleted && status === 'none') {
        return (
            <div className="w-5 h-5 flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
        )
    }

    // Не записан (будущая) - стрелка вправо с палочкой
    return (
        <div className={`${iconClass} border-gray-400`}>
            <svg className={`${svgClass} text-gray-400`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
        </div>
    )
}

export default function MiniActivityCard({ activity }) {
    const navigate = useNavigate()

    const handleCardClick = () => {
        navigate(`/activity/${activity.id}`)
    }

    // Получить статус
    const getStatus = () => {
        if (activity.attended) return 'attended'
        if (activity.isPending) return 'pending'
        if (activity.isJoined) return 'registered'
        return 'none'
    }

    // Получить текст дистанции/набора
    const getDistanceText = () => {
        const parts = []
        if (activity.distance) parts.push(`${activity.distance} км`)
        if (activity.elevation) parts.push(`↗${activity.elevation} м`)
        return parts.length > 0 ? ` · ${parts.join(' · ')}` : ''
    }

    // Opacity для завершённых
    const isConfirmedPast = activity.participationStatus === 'attended' || activity.participationStatus === 'missed'
    const isCompletedNotJoined = activity.isCompleted && !activity.isJoined && !activity.participationStatus

    return (
        <div
            onClick={handleCardClick}
            className={`bg-white border border-gray-200 rounded-xl p-3 cursor-pointer hover:border-gray-300 transition-colors ${isConfirmedPast || isCompletedNotJoined ? 'opacity-50' : ''}`}
        >
            <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0 pr-2">
                    <h4 className="text-sm text-gray-800 font-medium truncate">{activity.title}</h4>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                        {formatDate(activity.date)}, {formatTime(activity.date)} · {activity.location}
                        {getDistanceText()}
                    </p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-base">{activity.icon}</span>
                    <MiniStatusIcon
                        status={getStatus()}
                        isCompleted={activity.isCompleted}
                        participationStatus={activity.participationStatus}
                    />
                </div>
            </div>
        </div>
    )
}
