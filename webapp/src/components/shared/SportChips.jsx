import React from 'react'
import { sportTypes } from '../../data/sample_data'

export default function SportChips({
    selected = [],
    onChange,
    multiple = true,
    label = 'Тип'
}) {
    const handleClick = (sportId) => {
        if (multiple) {
            // Multi-select mode
            if (selected.includes(sportId)) {
                onChange(selected.filter(id => id !== sportId))
            } else {
                onChange([...selected, sportId])
            }
        } else {
            // Single-select mode
            onChange(sportId)
        }
    }

    const isSelected = (sportId) => {
        if (multiple) {
            return selected.includes(sportId)
        }
        return selected === sportId
    }

    return (
        <div className="mb-4">
            {label && (
                <label className="text-sm text-gray-700 mb-2 block">{label}</label>
            )}
            <div className="flex flex-wrap gap-2">
                {sportTypes.map(sport => (
                    <button
                        key={sport.id}
                        onClick={() => handleClick(sport.id)}
                        className={`px-4 py-2 rounded-lg border text-sm flex items-center gap-2 transition-colors ${isSelected(sport.id)
                                ? 'border-gray-800 bg-gray-800 text-white'
                                : 'border-gray-200 text-gray-600 hover:border-gray-300'
                            }`}
                    >
                        <span>{sport.icon}</span>
                        <span>{sport.label}</span>
                    </button>
                ))}
            </div>
        </div>
    )
}
