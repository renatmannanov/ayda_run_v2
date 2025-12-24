import React from 'react'
import { Avatar } from '../ui'

/**
 * Compact club/group card for horizontal scroll in profile
 *
 * @param {Object} props
 * @param {Object} props.item - Club or group object
 * @param {function} props.onClick - Click handler
 */
export default function ClubGroupCard({ item, onClick }) {
    return (
        <button
            onClick={onClick}
            className="flex flex-col items-center gap-1 min-w-[64px]"
        >
            <Avatar
                src={item.photo}
                name={item.name}
                size="lg"
                forcePhoto
            />
            <span className="text-xs text-gray-600 max-w-[64px] truncate text-center">
                {item.name}
            </span>
        </button>
    )
}
