import React from 'react'
import { SPORT_TYPES } from '../constants/sports'
import { Avatar } from './ui'

// Strava Icon Component
const StravaIcon = ({ url }) => {
    if (!url) return <div className="w-6" /> // Placeholder for alignment
    return (
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="w-6 h-6 rounded bg-orange-500 flex items-center justify-center text-white text-xs font-bold hover:bg-orange-600 transition-colors flex-shrink-0"
        >
            S
        </a>
    )
}

export default function ParticipantsSheet({
    isOpen,
    onClose,
    participants = [],
    title = 'Участники',
    maxParticipants = null,
    isCompleted = false,
    attendedCount = null,
    actionButton = null
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
        if (isCompleted && attendedCount !== null) {
            return `${attendedCount}/${participants.length} были`
        }
        if (maxParticipants) {
            return `${participants.length}/${maxParticipants}`
        }
        return participants.length.toString()
    }

    // Sort participants: organizer first, then others
    const sortedParticipants = [...participants].sort((a, b) => {
        if (a.isOrganizer && !b.isOrganizer) return -1
        if (!a.isOrganizer && b.isOrganizer) return 1
        return 0
    })

    return (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex flex-col justify-end"
            onClick={onClose}
        >
            <div
                className="bg-white w-full max-w-md mx-auto rounded-t-2xl flex flex-col"
                onClick={e => e.stopPropagation()}
                style={{ maxHeight: '50vh' }}
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
                <div className="flex-1 overflow-auto px-4 py-2">
                    {sortedParticipants.length === 0 ? (
                        <div className="py-8 text-center text-sm text-gray-400">
                            Пока никто не записался
                        </div>
                    ) : (
                        sortedParticipants.map(participant => {
                            const sportIcons = getSportIcons(participant.preferredSports)
                            return (
                                <div
                                    key={participant.id}
                                    className={`flex items-center py-3 border-b border-gray-100 last:border-0 ${isCompleted && participant.attended === false ? 'opacity-50' : ''}`}
                                >
                                    {/* Avatar */}
                                    <Avatar
                                        src={participant.photo}
                                        name={participant.name}
                                        size="md"
                                        className="mr-3 flex-shrink-0"
                                        showPhoto={participant.showPhoto}
                                    />

                                    {/* Name + Sports - left side */}
                                    <div className="flex items-center gap-2 flex-1 min-w-0">
                                        <span className={`text-sm ${isCompleted && participant.attended === false
                                            ? 'text-gray-400 line-through'
                                            : 'text-gray-700'
                                            }`}>
                                            {participant.name}
                                        </span>

                                        {/* Sports */}
                                        {sportIcons.length > 0 && (
                                            <div className="flex gap-0.5 flex-shrink-0">
                                                {sportIcons.map((icon, idx) => (
                                                    <span key={idx} className="text-sm">{icon}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Organizer badge - right side near Strava */}
                                    {participant.isOrganizer && (
                                        <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded mr-2 flex-shrink-0">
                                            Орг
                                        </span>
                                    )}

                                    {/* Completed activity attendance indicator */}
                                    {isCompleted && (
                                        <span className="text-xs text-gray-400 mr-2">
                                            {participant.attended === true && '✓'}
                                            {participant.attended === false && '—'}
                                        </span>
                                    )}

                                    {/* Strava - right aligned */}
                                    <StravaIcon url={participant.stravaLink} />
                                </div>
                            )
                        })
                    )}
                </div>
            </div>

            {/* Action Button Area - stays visible below popup */}
            {actionButton && (
                <div className="bg-white w-full max-w-md mx-auto px-4 pb-6 pt-4 border-t border-gray-200">
                    {actionButton}
                </div>
            )}
        </div>
    )
}
