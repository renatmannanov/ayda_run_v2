import React from 'react'
import { useNavigate } from 'react-router-dom'
import { formatTime, formatDate } from '../../data/sample_data'

export default function ActivityCard({ activity, onJoinToggle }) {
    const navigate = useNavigate()
    const isFull = activity.maxParticipants !== null && activity.participants >= activity.maxParticipants

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
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">
                    <span className="text-lg">✓</span>
                </div>
            )
        }

        if (isFull) {
            return <span className="text-sm text-gray-400">Мест нет</span>
        }

        return (
            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-600">
                <span className="text-lg">+</span>
            </div>
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
                    {activity.maxParticipants !== null
                        ? `${activity.participants}/${activity.maxParticipants}`
                        : `${activity.participants}`}
                    {(activity.club || activity.group) && (
                        <> · {activity.club || activity.group}</>
                    )}
                </span>
                {renderActionButton()}
            </div>
        </div>
    )
}
