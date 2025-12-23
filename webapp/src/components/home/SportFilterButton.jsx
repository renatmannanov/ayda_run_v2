import React from 'react'

/**
 * Equalizer-style filter button for sport types
 * Shows badge with count when filters are active
 */
export function SportFilterButton({ selectedCount = 0, onClick }) {
    const hasFilters = selectedCount > 0

    return (
        <button
            onClick={onClick}
            className={`relative p-1 rounded-lg transition-colors ${
                hasFilters
                    ? 'text-gray-800'
                    : 'text-gray-400 hover:text-gray-600'
            }`}
            aria-label="Фильтр по видам спорта"
        >
            {/* Equalizer icon - 3 vertical lines with circles (30% smaller) */}
            <svg
                className="w-3.5 h-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2.5}
                strokeLinecap="round"
            >
                {/* Left line with dot */}
                <line x1="4" y1="4" x2="4" y2="20" />
                <circle cx="4" cy="14" r="2.5" fill="currentColor" stroke="none" />

                {/* Middle line with dot */}
                <line x1="12" y1="4" x2="12" y2="20" />
                <circle cx="12" cy="8" r="2.5" fill="currentColor" stroke="none" />

                {/* Right line with dot */}
                <line x1="20" y1="4" x2="20" y2="20" />
                <circle cx="20" cy="16" r="2.5" fill="currentColor" stroke="none" />
            </svg>

            {/* Badge with count */}
            {hasFilters && (
                <span className="absolute -top-1 -right-1.5 min-w-[14px] h-[14px] bg-blue-500 text-white text-[9px] font-medium rounded-full flex items-center justify-center px-0.5">
                    {selectedCount}
                </span>
            )}
        </button>
    )
}
