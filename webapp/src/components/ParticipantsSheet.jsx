import React from 'react'

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
                className="bg-white w-full max-w-md rounded-t-2xl max-h-[60vh] flex flex-col mb-16"
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
                    {participants.map(participant => (
                        <div
                            key={participant.id}
                            className={`flex items-center justify-between py-3 ${isPast && participant.attended === false ? 'opacity-50' : ''
                                }`}
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-2xl">{participant.avatar}</span>
                                <span className={`text-sm ${isPast && participant.attended === false
                                    ? 'text-gray-400 line-through'
                                    : 'text-gray-700'
                                    }`}>
                                    {participant.name}
                                </span>
                            </div>
                            <span className="text-xs text-gray-400">
                                {participant.isOrganizer && 'организатор'}
                                {isPast && participant.attended === true && '✓'}
                                {isPast && participant.attended === false && '—'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
