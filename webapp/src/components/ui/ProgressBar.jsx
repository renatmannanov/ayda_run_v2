import React from 'react'

/**
 * Progress bar component with optional percentage display
 *
 * @param {Object} props
 * @param {number} props.value - Current value
 * @param {number} props.max - Maximum value
 * @param {boolean} props.showPercent - Show percentage label (default: true)
 */
export default function ProgressBar({ value, max, showPercent = true }) {
    const percent = max > 0 ? Math.round((value / max) * 100) : 0

    return (
        <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                    className="h-full bg-gray-300 rounded-full transition-all duration-300"
                    style={{ width: `${percent}%` }}
                />
            </div>
            {showPercent && (
                <span className="text-sm text-gray-400 w-12 text-right">{percent}%</span>
            )}
        </div>
    )
}
