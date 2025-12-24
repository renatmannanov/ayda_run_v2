import React from 'react'

/**
 * Search button with magnifying glass icon
 * Simple line-style icon matching SportFilterButton
 */
export function SearchButton({ onClick, isActive = false }) {
    return (
        <button
            onClick={onClick}
            className={`relative p-1 rounded-lg transition-colors ${
                isActive
                    ? 'text-gray-800'
                    : 'text-gray-400 hover:text-gray-600'
            }`}
            aria-label="Поиск"
        >
            {/* Magnifying glass icon - simple line style */}
            <svg
                className="w-3.5 h-3.5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
            >
                <circle cx="10" cy="10" r="6" />
                <line x1="14.5" y1="14.5" x2="20" y2="20" />
            </svg>
        </button>
    )
}
