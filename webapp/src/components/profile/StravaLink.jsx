import React from 'react'

/**
 * Strava connection status component
 * Shows connected badge or "Connect Strava" button
 *
 * @param {Object} props
 * @param {boolean} props.connected - Whether Strava OAuth is connected
 * @param {function} props.onAdd - Callback when "Connect" button is clicked
 */
export default function StravaLink({ connected, onAdd }) {
    if (connected) {
        return (
            <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-5 h-5 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">
                    S
                </span>
                <span>Strava</span>
                <svg
                    className="w-4 h-4 text-green-500 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            </div>
        )
    }

    // Show "Connect Strava" button
    return (
        <button
            onClick={onAdd}
            className="flex items-center gap-2 text-sm text-orange-500 hover:text-orange-600 transition-colors"
        >
            <span className="w-5 h-5 rounded bg-orange-100 text-orange-500 text-xs font-bold flex items-center justify-center flex-shrink-0">
                S
            </span>
            <span>Подключить Strava</span>
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
