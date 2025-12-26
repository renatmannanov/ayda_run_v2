import React from 'react'

export function ModeToggle({ mode, onModeChange, title }) {
    return (
        <div className="flex items-baseline gap-4">
            {/* Page title */}
            <h1 className="text-sm font-medium text-gray-800">{title}</h1>

            {/* Tabs */}
            <div className="flex items-baseline gap-3 text-sm">
                <button
                    onClick={() => onModeChange('my')}
                    className={`transition-colors ${
                        mode === 'my'
                            ? 'text-gray-900 font-medium border-b border-gray-800'
                            : 'text-gray-400 hover:text-gray-600'
                    }`}
                >
                    Мои
                </button>
                <button
                    onClick={() => onModeChange('all')}
                    className={`transition-colors ${
                        mode === 'all'
                            ? 'text-gray-900 font-medium border-b border-gray-800'
                            : 'text-gray-400 hover:text-gray-600'
                    }`}
                >
                    Все
                </button>
            </div>
        </div>
    )
}
