import React from 'react'
import { useNavigate } from 'react-router-dom'
import { pluralizeMembers } from '../data/sample_data'

export default function GroupCard({ group, showJoinButton = false, onJoin }) {
    const navigate = useNavigate()

    const handleClick = () => {
        navigate(`/group/${group.id}`)
    }

    const handleJoinClick = (e) => {
        e.stopPropagation()
        if (onJoin) onJoin(group)
    }

    return (
        <div
            onClick={handleClick}
            className="bg-white border border-gray-200 rounded-xl p-4 mb-3 cursor-pointer hover:border-gray-300 transition-colors"
        >
            <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                    <span className="text-xl flex-shrink-0">{group.icon || '👥'}</span>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                            <h3 className="text-base text-gray-800 font-medium truncate flex-1 min-w-0">
                                <span className={group.club_name || group.parentClub ? "" : "truncate"}>
                                    {group.name}
                                </span>
                                {(group.club_name || group.parentClub) && (
                                    <span className="text-gray-400 font-normal truncate"> / {group.club_name || group.parentClub}</span>
                                )}
                            </h3>
                            {group.isMember && !showJoinButton && (
                                <span className="text-green-600 text-sm flex-shrink-0">✓</span>
                            )}
                        </div>
                        <p className="text-sm text-gray-500 mt-1 truncate">
                            {pluralizeMembers(group.members)}
                        </p>
                    </div>
                </div>

                {showJoinButton && (
                    <button
                        onClick={handleJoinClick}
                        className="text-sm text-gray-600 hover:text-gray-800 transition-colors ml-2"
                    >
                        Вступить
                    </button>
                )}
            </div>
        </div>
    )
}
