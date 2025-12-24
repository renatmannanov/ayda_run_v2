import React from 'react'
import { SPORT_TYPES } from '../../constants/sports'

/**
 * Bottom sheet popup for filtering activities
 * Supports filtering by clubs/groups and sport types
 */
export function ActivityFilterPopup({
    isOpen,
    onClose,
    // Clubs & Groups
    myClubs = [],
    myGroups = [],
    selectedClubs = [],
    selectedGroups = [],
    onToggleClub,
    onToggleGroup,
    // Sports
    selectedSports = [],
    onToggleSport,
    // Clear all
    onClear
}) {
    if (!isOpen) return null

    const hasFilters = selectedClubs.length > 0 || selectedGroups.length > 0 || selectedSports.length > 0
    const hasClubsOrGroups = myClubs.length > 0 || myGroups.length > 0

    return (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/30"
                onClick={onClose}
            />

            {/* Popup - fixed height to avoid jumping */}
            <div className="relative bg-white rounded-t-2xl w-full max-w-md p-4 pb-6 animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-base font-medium text-gray-800">
                        Фильтры
                    </h3>
                    <div className="flex items-center gap-2">
                        {/* Compact reset button - always visible space reserved */}
                        <button
                            onClick={onClear}
                            className={`text-xs transition-colors ${
                                hasFilters
                                    ? 'text-gray-400 hover:text-gray-600'
                                    : 'text-transparent pointer-events-none'
                            }`}
                        >
                            Сбросить
                        </button>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 p-1 -mr-1"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Scrollable content */}
                <div className="max-h-[50vh] overflow-y-auto">
                    {/* Clubs & Groups section */}
                    {hasClubsOrGroups && (
                        <div className="mb-4">
                            <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">
                                Клубы и группы
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {/* Clubs */}
                                {myClubs.map(club => (
                                    <button
                                        key={`club-${club.id}`}
                                        onClick={() => onToggleClub(club.id)}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors ${
                                            selectedClubs.includes(club.id)
                                                ? 'bg-gray-800 text-white'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                    >
                                        {club.avatar ? (
                                            <img
                                                src={club.avatar}
                                                alt=""
                                                className="w-4 h-4 rounded-full object-cover"
                                            />
                                        ) : (
                                            <span className="w-4 h-4 rounded-full bg-gray-300 flex items-center justify-center text-[10px]">
                                                🏆
                                            </span>
                                        )}
                                        <span className="max-w-[100px] truncate">{club.name}</span>
                                    </button>
                                ))}

                                {/* Groups */}
                                {myGroups.map(group => (
                                    <button
                                        key={`group-${group.id}`}
                                        onClick={() => onToggleGroup(group.id)}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors ${
                                            selectedGroups.includes(group.id)
                                                ? 'bg-gray-800 text-white'
                                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                        }`}
                                    >
                                        {group.avatar ? (
                                            <img
                                                src={group.avatar}
                                                alt=""
                                                className="w-4 h-4 rounded-full object-cover"
                                            />
                                        ) : (
                                            <span className="w-4 h-4 rounded-full bg-gray-300 flex items-center justify-center text-[10px]">
                                                👥
                                            </span>
                                        )}
                                        <span className="max-w-[100px] truncate">{group.name}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Sport types section */}
                    <div>
                        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">
                            Вид спорта
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {SPORT_TYPES.map(sport => (
                                <button
                                    key={sport.id}
                                    onClick={() => onToggleSport(sport.id)}
                                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors ${
                                        selectedSports.includes(sport.id)
                                            ? 'bg-gray-800 text-white'
                                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                                >
                                    <span>{sport.icon}</span>
                                    <span>{sport.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
