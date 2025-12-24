import React from 'react'

/**
 * Dialog for selecting scope when editing/cancelling recurring activities
 *
 * @param {boolean} isOpen - Whether dialog is visible
 * @param {function} onClose - Called when dialog is dismissed
 * @param {function} onSelect - Called with selected scope ('this_only' | 'this_and_following' | 'entire_series')
 * @param {string} mode - 'edit' or 'cancel'
 * @param {boolean} loading - Whether action is in progress
 */
export default function RecurringScopeDialog({
    isOpen,
    onClose,
    onSelect,
    mode = 'edit',
    loading = false
}) {
    if (!isOpen) return null

    const title = mode === 'edit'
        ? 'Редактировать тренировку'
        : 'Отменить тренировку'

    const description = 'Это повторяющаяся тренировка. Выберите, что изменить:'

    const options = mode === 'edit'
        ? [
            {
                id: 'this_only',
                label: 'Только эту',
                description: 'Изменить только эту тренировку'
            },
            {
                id: 'this_and_following',
                label: 'Эту и следующие',
                description: 'Изменить эту и все будущие'
            }
        ]
        : [
            {
                id: 'this_only',
                label: 'Только эту',
                description: 'Отменить только эту тренировку'
            },
            {
                id: 'entire_series',
                label: 'Всю серию',
                description: 'Отменить все будущие тренировки'
            }
        ]

    return (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={onClose}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl p-6"
                onClick={e => e.stopPropagation()}
            >
                <h3 className="text-base font-medium text-gray-800 mb-2">
                    {title}
                </h3>
                <p className="text-sm text-gray-500 mb-4">
                    {description}
                </p>

                <div className="space-y-2">
                    {options.map(option => (
                        <button
                            key={option.id}
                            onClick={() => onSelect(option.id)}
                            disabled={loading}
                            className="w-full text-left p-4 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors disabled:opacity-50"
                        >
                            <span className="text-sm font-medium text-gray-800">
                                {option.label}
                            </span>
                            <span className="block text-xs text-gray-400 mt-0.5">
                                {option.description}
                            </span>
                        </button>
                    ))}
                </div>

                <button
                    onClick={onClose}
                    disabled={loading}
                    className="w-full mt-4 py-3 text-gray-400 text-sm"
                >
                    Отмена
                </button>
            </div>
        </div>
    )
}
