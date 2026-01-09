import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '../api'

export default function CreateMenu({ isOpen, onClose, context = null }) {
    const navigate = useNavigate()
    const [counts, setCounts] = useState(null)
    const [loading, setLoading] = useState(false)

    // Fetch counts when menu opens
    useEffect(() => {
        if (isOpen && !counts) {
            setLoading(true)
            usersApi.getCounts()
                .then(setCounts)
                .catch(console.error)
                .finally(() => setLoading(false))
        }
    }, [isOpen, counts])

    if (!isOpen) return null

    const menuItems = [
        {
            icon: '🏆',
            label: 'Клуб',
            path: '/club/create',
            countKey: 'clubs'
        },
        {
            icon: '👥',
            label: 'Группу',
            path: '/group/create',
            countKey: 'groups'
        },
        {
            icon: '🏃',
            label: 'Активность',
            path: '/activity/create',
            countKey: 'activities_upcoming'
        }
    ]

    const handleItemClick = (path, isDisabled) => {
        if (isDisabled) return
        onClose()
        navigate(path, { state: context })
    }

    return (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={onClose}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl px-4 pt-4 pb-6"
                onClick={e => e.stopPropagation()}
            >
                <h3 className="text-sm font-medium text-gray-500 mb-2 px-2">Создать</h3>

                {menuItems.map(item => {
                    const countData = counts?.[item.countKey]
                    const current = countData?.current ?? 0
                    const max = countData?.max ?? 999
                    const isDisabled = current >= max

                    return (
                        <button
                            key={item.path}
                            onClick={() => handleItemClick(item.path, isDisabled)}
                            disabled={isDisabled}
                            className={`w-full text-left py-2.5 flex items-center gap-3 rounded-lg px-2 transition-colors ${
                                isDisabled
                                    ? 'opacity-50 cursor-not-allowed'
                                    : 'hover:bg-gray-50'
                            }`}
                        >
                            <span className="text-lg">{item.icon}</span>
                            <div className="flex-1">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className={`text-sm ${isDisabled ? 'text-gray-400' : 'text-gray-700'}`}>
                                            {item.label}
                                        </span>
                                        {isDisabled && (
                                            <span className="text-xs text-gray-400">· лимит достигнут</span>
                                        )}
                                    </div>
                                    {counts && (
                                        <span className={`text-xs ${isDisabled ? 'text-gray-400' : 'text-gray-500'}`}>
                                            {current}/{max}
                                        </span>
                                    )}
                                </div>
                                {/* Context info for activity */}
                                {context?.name && item.path === '/activity/create' && !isDisabled && (
                                    <p className="text-xs text-gray-400">в {context.name}</p>
                                )}
                            </div>
                        </button>
                    )
                })}

                <button
                    onClick={onClose}
                    className="w-full mt-2 py-2 text-gray-400 text-sm hover:text-gray-600 transition-colors"
                >
                    Отмена
                </button>
            </div>
        </div>
    )
}
