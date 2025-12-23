import React, { useState } from 'react'

export default function DropdownPicker({
    value,
    options,
    onChange,
    placeholder = 'Выбрать...',
    disabled = false
}) {
    const [isOpen, setIsOpen] = useState(false)
    const selectedOption = options.find(o => o.id === value)

    const handleSelect = (optionId) => {
        onChange(optionId)
        setIsOpen(false)
    }

    return (
        <div className="relative">
            <button
                type="button"
                onClick={() => !disabled && setIsOpen(!isOpen)}
                disabled={disabled}
                className={`w-full px-4 py-3 border rounded-xl text-sm text-left flex items-center justify-between transition-colors ${
                    disabled
                        ? 'border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed'
                        : 'border-gray-200 hover:border-gray-300'
                }`}
            >
                <div className="flex items-center gap-2">
                    {selectedOption?.icon && <span>{selectedOption.icon}</span>}
                    <span className={selectedOption ? 'text-gray-800' : 'text-gray-400'}>
                        {selectedOption?.label || placeholder}
                    </span>
                    {selectedOption?.sublabel && (
                        <span className="text-gray-400">· {selectedOption.sublabel}</span>
                    )}
                </div>
                {!disabled && (
                    <svg
                        className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                )}
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-20 overflow-hidden max-h-64 overflow-y-auto">
                        {options.map(option => (
                            <button
                                key={option.id}
                                type="button"
                                onClick={() => handleSelect(option.id)}
                                className={`w-full px-4 py-3 text-sm text-left flex items-center gap-2 hover:bg-gray-50 transition-colors ${
                                    value === option.id ? 'bg-gray-50' : ''
                                }`}
                            >
                                {option.icon && <span>{option.icon}</span>}
                                <div className="flex-1">
                                    <span className="text-gray-800">{option.label}</span>
                                    {option.sublabel && (
                                        <span className="text-gray-400 ml-1">· {option.sublabel}</span>
                                    )}
                                </div>
                                {value === option.id && (
                                    <svg
                                        className="w-5 h-5 text-gray-800"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                        strokeWidth={2}
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                    </svg>
                                )}
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    )
}
