import React from 'react'
import { SPORT_TYPES } from '../../constants/sports'

/**
 * Bottom sheet popup for selecting sport type filters
 * Supports multiple selection
 */
export function SportFilterPopup({
    isOpen,
    onClose,
    selectedSports = [],
    onToggle,
    onClear
}) {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/30"
                onClick={onClose}
            />

            {/* Popup */}
            <div className="relative bg-white rounded-t-2xl w-full max-w-md p-4 pb-8 animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-medium text-gray-800">
                        Фильтр по спорту
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 p-1 -mr-1"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Sport pills */}
                <div className="flex flex-wrap gap-2">
                    {SPORT_TYPES.map(sport => (
                        <button
                            key={sport.id}
                            onClick={() => onToggle(sport.id)}
                            className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-sm transition-colors ${
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

                {/* Reset button - appears when filters are active */}
                {selectedSports.length > 0 && (
                    <div className="flex justify-center mt-4">
                        <button
                            onClick={onClear}
                            className="flex items-center gap-1.5 px-3 py-2 rounded-full text-sm text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            <span>Сбросить</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
