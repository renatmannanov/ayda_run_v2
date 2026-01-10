import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const BANNER_DISMISSED_KEY = 'ayda_welcome_banner_dismissed'

/**
 * Welcome banner shown to new users who have clubs but no activities yet.
 * Shows once per user (dismissed state saved to localStorage).
 */
export function WelcomeBanner({ club, onDismiss }) {
    const navigate = useNavigate()
    const [isVisible, setIsVisible] = useState(true)

    // Check if banner was already dismissed
    useEffect(() => {
        const dismissed = localStorage.getItem(BANNER_DISMISSED_KEY)
        if (dismissed) {
            setIsVisible(false)
        }
    }, [])

    const handleDismiss = () => {
        localStorage.setItem(BANNER_DISMISSED_KEY, 'true')
        setIsVisible(false)
        onDismiss?.()
    }

    const handleGoToClub = (e) => {
        e.preventDefault()
        e.stopPropagation()
        localStorage.setItem(BANNER_DISMISSED_KEY, 'true')
        navigate(`/club/${club.id}`)
    }

    if (!isVisible || !club) {
        return null
    }

    return (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 mb-4 relative">
            {/* Dismiss button */}
            <button
                onClick={handleDismiss}
                className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 p-1"
                aria-label="Закрыть"
            >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>

            {/* Content */}
            <div className="flex items-start gap-3 pr-6">
                <div className="text-2xl">🎉</div>
                <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-1">
                        Добро пожаловать в клуб!
                    </h3>
                    <p className="text-sm text-gray-600 mb-3">
                        Ты участник клуба «{club.name}». Переходи, чтобы увидеть расписание тренировок.
                    </p>
                    <button
                        onClick={handleGoToClub}
                        className="inline-flex items-center gap-1 text-sm font-medium text-green-600 hover:text-green-700"
                    >
                        Перейти в клуб
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    )
}

export default WelcomeBanner
