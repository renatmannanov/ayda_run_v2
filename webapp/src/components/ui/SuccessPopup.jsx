import React from 'react'
import { Button } from './index'

/**
 * Success Popup - Universal success screen for all create flows
 *
 * Props:
 * - isOpen: boolean
 * - title: string (e.g. "Тренировка создана!")
 * - description?: string
 * - onDone: () => void
 * - doneButtonText?: string (default: "Готово")
 * - shareLink?: string (for clubs/groups)
 * - onCopyLink?: () => void
 * - onShare?: () => void
 */
export default function SuccessPopup({
    isOpen,
    title,
    description,
    onDone,
    doneButtonText = 'Готово',
    shareLink,
    onCopyLink,
    onShare
}) {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/40" />

            {/* Modal */}
            <div className="relative bg-white rounded-2xl w-full max-w-sm p-6 text-center">
                {/* Success icon */}
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-4 mx-auto">
                    <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                </div>

                {/* Title */}
                <h3 className="text-lg font-medium text-gray-800">{title}</h3>

                {/* Description */}
                {description && (
                    <p className="text-sm text-gray-500 mt-2">{description}</p>
                )}

                {/* Share link section */}
                {shareLink && (
                    <div className="mt-6">
                        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
                            <p className="text-xs text-gray-400 mb-2">Ссылка для приглашения</p>
                            <p className="text-sm text-gray-800 break-all">{shareLink}</p>
                        </div>

                        <div className="flex gap-3">
                            {onCopyLink && (
                                <button
                                    onClick={onCopyLink}
                                    className="flex-1 py-3 border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors"
                                >
                                    Копировать
                                </button>
                            )}
                            {onShare && (
                                <button
                                    onClick={onShare}
                                    className="flex-1 py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
                                >
                                    Поделиться
                                </button>
                            )}
                        </div>
                    </div>
                )}

                {/* Done button */}
                <button
                    onClick={onDone}
                    className={`w-full py-3 rounded-xl text-sm font-medium transition-colors ${
                        shareLink
                            ? 'mt-4 text-gray-500 hover:text-gray-700'
                            : 'mt-6 bg-gray-800 text-white hover:bg-gray-700'
                    }`}
                >
                    {doneButtonText}
                </button>
            </div>
        </div>
    )
}
