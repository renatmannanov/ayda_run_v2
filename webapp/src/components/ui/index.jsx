import React from 'react'

export { default as Avatar } from './Avatar'
export { default as AvatarStack } from './AvatarStack'
export { default as GpxUpload } from './GpxUpload'

export function Loading({ text = 'Загрузка...' }) {
    return (
        <div className="flex-1 flex flex-col items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-gray-200 border-t-gray-800 rounded-full animate-spin mb-4" />
            <p className="text-sm text-gray-500">{text}</p>
        </div>
    )
}

export function LoadingScreen({ text = 'Загрузка...' }) {
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
                <div className="w-10 h-10 border-2 border-gray-200 border-t-gray-800 rounded-full animate-spin mb-4 mx-auto" />
                <p className="text-sm text-gray-500">{text}</p>
            </div>
        </div>
    )
}

export function ErrorMessage({ message = 'Что-то пошло не так', onRetry }) {
    return (
        <div className="flex-1 flex flex-col items-center justify-center py-12 px-6 text-center">
            <span className="text-4xl mb-4">😵</span>
            <h2 className="text-base text-gray-700 mb-2">Ошибка</h2>
            <p className="text-sm text-gray-500 mb-6">{message}</p>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                    Попробовать снова →
                </button>
            )}
        </div>
    )
}

export function ErrorScreen({ message = 'Что-то пошло не так', onRetry }) {
    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-6">
            <div className="text-center">
                <span className="text-5xl mb-4 block">😵</span>
                <h2 className="text-lg text-gray-700 mb-2">Ошибка</h2>
                <p className="text-sm text-gray-500 mb-6">{message}</p>
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="px-6 py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
                    >
                        Попробовать снова
                    </button>
                )}
            </div>
        </div>
    )
}

export function EmptyState({
    icon = '📭',
    title = 'Пусто',
    description,
    actionText,
    onAction
}) {
    return (
        <div className="flex-1 flex flex-col items-center justify-center py-12 px-6 text-center">
            <span className="text-4xl mb-4">{icon}</span>
            <h2 className="text-base text-gray-700 mb-2">{title}</h2>
            {description && (
                <p className="text-sm text-gray-500 mb-6">{description}</p>
            )}
            {actionText && onAction && (
                <button
                    onClick={onAction}
                    className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                    {actionText} →
                </button>
            )}
        </div>
    )
}

export function Button({
    children,
    onClick,
    variant = 'primary',
    disabled = false,
    loading = false,
    className = ''
}) {
    const baseStyles = 'w-full py-4 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2'

    const variants = {
        primary: 'bg-gray-800 text-white hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed',
        secondary: 'bg-gray-100 text-gray-600 hover:bg-gray-200',
        success: 'bg-green-50 text-green-600',
        outline: 'border border-gray-200 text-gray-700 hover:bg-gray-50'
    }

    return (
        <button
            onClick={onClick}
            disabled={disabled || loading}
            className={`${baseStyles} ${variants[variant]} ${className}`}
        >
            {loading && (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            )}
            {children}
        </button>
    )
}

export function Toast({ message, type = 'info', onClose }) {
    const colors = {
        info: 'bg-gray-800 text-white',
        success: 'bg-green-600 text-white',
        error: 'bg-red-600 text-white',
        warning: 'bg-orange-500 text-white'
    }

    return (
        <div className={`fixed bottom-24 left-4 right-4 max-w-md mx-auto ${colors[type]} rounded-xl px-4 py-3 flex items-center justify-between shadow-lg z-50`}>
            <span className="text-sm">{message}</span>
            {onClose && (
                <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100">✕</button>
            )}
        </div>
    )
}
