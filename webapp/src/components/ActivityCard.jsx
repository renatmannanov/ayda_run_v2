import React from 'react'
import { useNavigate } from 'react-router-dom'
import { formatTime, formatDate } from '../data/sample_data'

export default function ActivityCard({ activity, onJoinToggle }) {
    const navigate = useNavigate()
    const isFull = activity.participants >= activity.maxParticipants

    const handleCardClick = () => {
        navigate(`/activity/${activity.id}`)
    }

    const handleActionClick = (e) => {
        e.stopPropagation()
        if (onJoinToggle) {
            onJoinToggle(activity.id)
        }
    }

    const renderActionButton = () => {
        if (activity.isPast) {
            return (
                <span className={`text-sm ${activity.attended ? 'text-gray-500' : 'text-gray-400'}`}>
                    {activity.attended ? 'Был ✓' : 'Пропустил'}
                </span>
            )
        }

        if (activity.isJoined) {
            return (
                <button
                    onClick={handleActionClick}
                    className="text-sm text-green-600 font-medium"
                >
                    Иду ✓
                </button>
            )
        }

        if (isFull) {
            return <span className="text-sm text-gray-400">Мест нет</span>
        }

        return (
            <button
                onClick={handleActionClick}
                className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
                Записаться
            </button>
        )
    }

    return (
        <div
            onClick={handleCardClick}
            className="bg-white border border-gray-200 rounded-xl p-4 mb-3 cursor-pointer hover:border-gray-300 transition-colors"
        >
            <div className="flex justify-between items-start mb-2">
                <h3 className="text-base text-gray-800 font-medium pr-2">
                    {activity.title}
                </h3>
                <span className="text-xl flex-shrink-0">{activity.icon}</span>
            </div>

            <p className="text-sm text-gray-500 mb-2">
                {formatDate(activity.date)}, {formatTime(activity.date)} · {activity.location}
            </p>

            <p className="text-sm text-gray-400 mb-3">
                {activity.distance} км · ↗{activity.elevation} м · {activity.duration}
            </p>

            <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">
                    {activity.participants}/{activity.maxParticipants}
                    {(activity.club || activity.group) && (
                        <> · {activity.club || activity.group}</>
                    )}
                </span>
                {renderActionButton()}
            </div>
        </div>
    )
}
