import React from 'react'

export function ModeToggle({ mode, onModeChange }) {
    return (
        <div className="flex items-center gap-1 text-sm">
            <button
                onClick={() => onModeChange('my')}
                className={`transition-colors ${
                    mode === 'my'
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-400 hover:text-gray-600'
                }`}
            >
                Мои
            </button>
            <span className="text-gray-300">/</span>
            <button
                onClick={() => onModeChange('all')}
                className={`transition-colors ${
                    mode === 'all'
                        ? 'text-gray-900 font-medium'
                        : 'text-gray-400 hover:text-gray-600'
                }`}
            >
                Все
            </button>
        </div>
    )
}
