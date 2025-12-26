import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

const navItems = [
    { path: '/clubs', icon: '👥', label: 'Клубы' },
    { path: '/profile', icon: '👤', label: 'Профиль', smallIcon: true },
    { path: '/', icon: '📅', label: 'Активности' }
]

export default function BottomNav({ onCreateClick }) {
    const navigate = useNavigate()
    const location = useLocation()

    return (
        <div className="bg-white border-t border-gray-200 py-3 pb-3 flex items-center justify-between safe-area-bottom" style={{ paddingLeft: '30px', paddingRight: '30px', paddingBottom: '12px' }}>
            {/* Create button - now first */}
            <button
                onClick={onCreateClick}
                className="w-9 h-9 rounded-full border-2 border-gray-800 flex items-center justify-center hover:bg-gray-100 transition-colors"
            >
                <svg className="w-4 h-4 text-gray-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m6-6H6" />
                </svg>
            </button>

            {/* Nav items */}
            {navItems.map(item => {
                const isActive = location.pathname === item.path
                return (
                    <button
                        key={item.path}
                        onClick={() => navigate(item.path)}
                        className={`flex flex-col items-center gap-1 transition-colors ${isActive ? 'text-gray-800' : 'text-gray-400 hover:text-gray-600'
                            }`}
                    >
                        <span className={`h-5 flex items-center justify-center ${item.smallIcon ? 'text-base' : 'text-lg'}`}>{item.icon}</span>
                        <span className={`text-xs ${isActive ? 'font-medium' : ''}`}>
                            {item.label}
                        </span>
                    </button>
                )
            })}
        </div>
    )
}
