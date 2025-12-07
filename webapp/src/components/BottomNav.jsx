import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

const navItems = [
    { path: '/', icon: '🏠', label: 'Home' },
    { path: '/clubs', icon: '👥', label: 'Клубы' },
    { path: '/profile', icon: '👤', label: 'Я' }
]

export default function BottomNav({ onCreateClick }) {
    const navigate = useNavigate()
    const location = useLocation()

    return (
        <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around safe-area-bottom">
            {navItems.map(item => {
                const isActive = location.pathname === item.path
                return (
                    <button
                        key={item.path}
                        onClick={() => navigate(item.path)}
                        className={`flex flex-col items-center gap-1 transition-colors ${isActive ? 'text-gray-800' : 'text-gray-400 hover:text-gray-600'
                            }`}
                    >
                        <span className="text-lg">{item.icon}</span>
                        <span className={`text-xs ${isActive ? 'font-medium' : ''}`}>
                            {item.label}
                        </span>
                    </button>
                )
            })}

            <button
                onClick={onCreateClick}
                className="w-10 h-10 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl hover:bg-gray-700 transition-colors"
            >
                ＋
            </button>
        </div>
    )
}
