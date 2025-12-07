import React from 'react'
import { useNavigate } from 'react-router-dom'

const menuItems = [
    { icon: '🏃', label: 'Тренировку', path: '/activity/create' },
    { icon: '🏆', label: 'Клуб', path: '/club/create' },
    { icon: '👥', label: 'Группу', path: '/group/create' }
]

export default function CreateMenu({ isOpen, onClose, context = null }) {
    const navigate = useNavigate()

    if (!isOpen) return null

    const handleItemClick = (path) => {
        onClose()
        navigate(path, { state: context })
    }

    return (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={onClose}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl p-6"
                onClick={e => e.stopPropagation()}
            >
                <h3 className="text-base font-medium text-gray-800 mb-4">Создать</h3>

                {menuItems.map(item => (
                    <button
                        key={item.path}
                        onClick={() => handleItemClick(item.path)}
                        className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2 transition-colors"
                    >
                        <span className="text-xl">{item.icon}</span>
                        <div>
                            <span className="text-gray-700">{item.label}</span>
                            {context?.name && item.path === '/activity/create' && (
                                <p className="text-xs text-gray-400">в {context.name}</p>
                            )}
                        </div>
                    </button>
                ))}

                <button
                    onClick={onClose}
                    className="w-full mt-4 py-3 text-gray-400 text-sm hover:text-gray-600 transition-colors"
                >
                    Отмена
                </button>
            </div>
        </div>
    )
}
