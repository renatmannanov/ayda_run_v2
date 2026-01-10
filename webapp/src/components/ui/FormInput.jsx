import React from 'react'

export function FormInput({
    label,
    value,
    onChange,
    placeholder,
    error,
    required,
    type = 'text',
    suffix,
    helper,
    disabled = false,
    name // Used for data-field attribute for scroll-to-error
}) {
    return (
        <div className="mb-4" data-field={name}>
            {label && (
                <label className="text-sm text-gray-700 mb-2 block">
                    {label} {required && <span className="text-red-400">*</span>}
                </label>
            )}
            <div className="relative">
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    disabled={disabled}
                    className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none transition-colors ${error ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
                        } ${disabled ? 'bg-gray-50 text-gray-400' : ''} ${suffix ? 'pr-12' : ''}`}
                />
                {suffix && (
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-400">
                        {suffix}
                    </span>
                )}
            </div>
            {helper && <p className="text-xs text-gray-400 mt-1">{helper}</p>}
        </div>
    )
}

export function FormTextarea({
    label,
    value,
    onChange,
    placeholder,
    rows = 3,
    error
}) {
    return (
        <div className="mb-4">
            {label && (
                <label className="text-sm text-gray-700 mb-2 block">{label}</label>
            )}
            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                rows={rows}
                className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none transition-colors resize-none ${error ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
                    }`}
            />
        </div>
    )
}

export function FormSelect({
    label,
    value,
    onClick,
    placeholder = 'Выбрать...',
    error,
    disabled = false
}) {
    return (
        <div className="mb-4">
            {label && (
                <label className="text-sm text-gray-700 mb-2 block">{label}</label>
            )}
            <button
                onClick={onClick}
                disabled={disabled}
                className={`w-full px-4 py-3 border rounded-xl text-sm text-left flex items-center justify-between transition-colors ${error ? 'border-red-300 bg-red-50' : 'border-gray-200 hover:border-gray-300'
                    } ${disabled ? 'bg-gray-50 text-gray-400' : ''}`}
            >
                <span className={value ? 'text-gray-800' : 'text-gray-400'}>
                    {value || placeholder}
                </span>
                <span className="text-gray-400">▾</span>
            </button>
        </div>
    )
}

export function FormCheckbox({ label, checked, onChange }) {
    return (
        <label className="flex items-center gap-2 cursor-pointer">
            <input
                type="checkbox"
                checked={checked}
                onChange={(e) => onChange(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300"
            />
            <span className="text-sm text-gray-600">{label}</span>
        </label>
    )
}

export function FormRadioGroup({ label, options, value, onChange }) {
    return (
        <div className="mb-4">
            {label && (
                <label className="text-sm text-gray-700 mb-3 block">{label}</label>
            )}
            <div className="space-y-2">
                {options.map(option => (
                    <button
                        key={option.id}
                        onClick={() => onChange(option.id)}
                        className={`w-full px-4 py-3 border rounded-xl text-left flex items-center gap-3 transition-colors ${value === option.id
                                ? 'border-gray-800 bg-gray-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                    >
                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${value === option.id ? 'border-gray-800' : 'border-gray-300'
                            }`}>
                            {value === option.id && <div className="w-2 h-2 rounded-full bg-gray-800" />}
                        </div>
                        <div>
                            <p className="text-sm text-gray-800">{option.label}</p>
                            {option.description && (
                                <p className="text-xs text-gray-500">{option.description}</p>
                            )}
                        </div>
                    </button>
                ))}
            </div>
        </div>
    )
}
