import React from 'react'
import { SPORT_TYPES } from '../constants/sports'

export default function ParticipantsSheet({
    isOpen,
    onClose,
    participants = [],
    title = 'Участники',
    maxParticipants = null,
    isPast = false,
    attendedCount = null
}) {
    if (!isOpen) return null

    // Helper to parse and get sport icons
    const getSportIcons = (preferredSports) => {
        try {
            if (!preferredSports) return []
            const sports = JSON.parse(preferredSports)
            return sports.map(sportId => {
                const sport = SPORT_TYPES.find(s => s.id === sportId)
                return sport?.icon || null
            }).filter(Boolean)
        } catch {
            return []
        }
    }

    const getSubtitle = () => {
        if (isPast && attendedCount !== null) {
            return `${attendedCount}/${participants.length} были`
        }
        if (maxParticipants) {
            return `${participants.length}/${maxParticipants}`
        }
        return participants.length.toString()
    }

    return (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={onClose}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl max-h-[60vh] flex flex-col"
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
                    <span className="text-base font-medium text-gray-800">
                        {title} · {getSubtitle()}
                    </span>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 text-xl"
                    >
                        ✕
                    </button>
                </div>

                {/* List */}
                <div className="flex-1 overflow-auto px-4 py-2 pb-6">
                    {participants.map(participant => {
                        const sportIcons = getSportIcons(participant.preferredSports)
                        return (
                            <div
                                key={participant.id}
                                className={`flex items-center justify-between py-3 ${isPast && participant.attended === false ? 'opacity-50' : ''
                                    }`}
                            >
                                <div className="flex items-center gap-3 flex-1">
                                    <span className="text-2xl">{participant.avatar}</span>
                                    <div className="flex items-center gap-2 flex-1">
                                        <span className={`text-sm ${isPast && participant.attended === false
                                            ? 'text-gray-400 line-through'
                                            : 'text-gray-700'
                                            }`}>
                                            {participant.name}
                                        </span>
                                        {participant.isOrganizer && (
                                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                                                Орг
                                            </span>
                                        )}
                                        {sportIcons.length > 0 && (
                                            <div className="flex gap-1">
                                                {sportIcons.map((icon, idx) => (
                                                    <span key={idx} className="text-sm">{icon}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <span className="text-xs text-gray-400">
                                    {isPast && participant.attended === true && '✓'}
                                    {isPast && participant.attended === false && '—'}
                                </span>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
