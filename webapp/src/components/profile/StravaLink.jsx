import React from 'react'

/**
 * Strava link display component
 * Shows link if connected, or "Add Strava" button if not
 *
 * @param {Object} props
 * @param {string|null} props.url - Strava profile URL
 * @param {function} props.onAdd - Callback when "Add" button is clicked
 */
export default function StravaLink({ url, onAdd }) {
    if (url) {
        // Format URL for display
        const displayUrl = url.replace(/^https?:\/\//, '')

        return (
            <a
                href={url.startsWith('http') ? url : `https://${url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-gray-500 hover:text-orange-500 transition-colors"
            >
                <span className="w-5 h-5 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">
                    S
                </span>
                <span className="truncate max-w-[180px]">{displayUrl}</span>
                <svg
                    className="w-4 h-4 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                </svg>
            </a>
        )
    }

    // Show "Add Strava" button
    return (
        <button
            onClick={onAdd}
            className="flex items-center gap-2 text-sm text-orange-500 hover:text-orange-600 transition-colors"
        >
            <span className="w-5 h-5 rounded bg-orange-100 text-orange-500 text-xs font-bold flex items-center justify-center flex-shrink-0">
                S
            </span>
            <span>Добавить Strava</span>
            <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
            >
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
        </button>
    )
}
