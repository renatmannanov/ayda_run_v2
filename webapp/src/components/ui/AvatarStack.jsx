import React from 'react'
import Avatar from './Avatar'

/**
 * AvatarStack component - displays overlapping avatars
 *
 * @param {Object} props
 * @param {Array} props.participants - Array of participant objects with {name, photo}
 * @param {number} props.max - Maximum number of avatars to show (default: 3)
 * @param {string} props.size - Avatar size: 'sm', 'md' (default: 'sm')
 */
export default function AvatarStack({ participants = [], max = 3, size = 'sm' }) {
    if (!participants || participants.length === 0) {
        return null
    }

    // Sort participants: organizer first, then others
    const sortedParticipants = [...participants].sort((a, b) => {
        if (a.isOrganizer && !b.isOrganizer) return -1
        if (!a.isOrganizer && b.isOrganizer) return 1
        return 0
    })

    const displayedParticipants = sortedParticipants.slice(0, max)
    const remainingCount = participants.length - max

    // Size mappings for the "+N" badge
    const badgeSizeClasses = {
        'sm': 'w-8 h-8 text-xs',
        'md': 'w-10 h-10 text-sm'
    }

    const badgeSize = badgeSizeClasses[size] || badgeSizeClasses.sm

    return (
        <div className="flex items-center">
            {displayedParticipants.map((participant, index) => (
                <div
                    key={participant.id || index}
                    className="border-2 border-white rounded-full"
                    style={{
                        marginLeft: index > 0 ? '-8px' : '0',
                        zIndex: displayedParticipants.length - index
                    }}
                >
                    <Avatar
                        src={participant.photo}
                        name={participant.name}
                        size={size}
                        showPhoto={participant.showPhoto}
                    />
                </div>
            ))}

            {remainingCount > 0 && (
                <div
                    className={`${badgeSize} rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-medium border-2 border-white`}
                    style={{
                        marginLeft: '-8px',
                        zIndex: 0
                    }}
                >
                    +{remainingCount}
                </div>
            )}
        </div>
    )
}
