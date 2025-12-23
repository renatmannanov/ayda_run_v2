import React from 'react'

export default function ToggleButtons({
    options,
    selected,
    onChange,
    hint,
    disabled = false
}) {
    return (
        <div>
            <div className="flex gap-2">
                {options.map(option => (
                    <button
                        key={option.id}
                        type="button"
                        onClick={() => !disabled && onChange(option.id)}
                        disabled={disabled}
                        className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm transition-colors ${
                            selected === option.id
                                ? 'bg-gray-800 text-white'
                                : disabled
                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                    >
                        {option.icon && <span>{option.icon}</span>}
                        <span>{option.label}</span>
                    </button>
                ))}
            </div>
            {hint && <p className="text-xs text-gray-400 mt-2">{hint}</p>}
        </div>
    )
}
