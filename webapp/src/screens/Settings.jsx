import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../contexts/UserContext'
import { LoadingScreen } from '../components/ui'

export default function Settings() {
    const navigate = useNavigate()
    const {
        user,
        isLoading,
        showPhoto,
        stravaConnected,
        updating,
        updateShowPhoto,
        connectStrava,
        disconnectStrava,
    } = useUser()

    if (isLoading) {
        return <LoadingScreen text="Загружаем настройки..." />
    }

    const handleTogglePhoto = async () => {
        await updateShowPhoto(!showPhoto)
    }

    const handleToggleStrava = async () => {
        if (stravaConnected) {
            if (!window.confirm('Отключить Strava? Автосинк тренировок перестанет работать.')) {
                return
            }
            await disconnectStrava()
        } else {
            await connectStrava()
        }
    }

    return (
        <div className="h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 flex-shrink-0">
                <button
                    onClick={() => navigate(-1)}
                    className="text-gray-500 hover:text-gray-700"
                >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                    </svg>
                </button>
                <h1 className="text-base font-medium text-gray-800">Настройки</h1>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-8">
                {/* Photo Toggle */}
                <div className="bg-white rounded-2xl p-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-800">
                                Показывать фото
                            </p>
                            <p className="text-xs text-gray-400 mt-0.5">
                                Вместо инициалов в аватарке
                            </p>
                        </div>
                        <button
                            onClick={handleTogglePhoto}
                            disabled={updating}
                            className={`w-12 h-7 rounded-full transition-colors relative ${
                                showPhoto ? 'bg-gray-800' : 'bg-gray-200'
                            } ${updating ? 'opacity-50' : ''}`}
                        >
                            <div className={`w-5 h-5 rounded-full bg-white shadow-sm transition-transform absolute top-1 ${
                                showPhoto ? 'left-6' : 'left-1'
                            }`} />
                        </button>
                    </div>
                </div>

                {/* Strava Toggle */}
                <div className="bg-white rounded-2xl p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="w-7 h-7 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">
                                S
                            </span>
                            <div>
                                <p className="text-sm font-medium text-gray-800">Strava</p>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {stravaConnected ? 'Подключена' : 'Автосинк тренировок'}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={handleToggleStrava}
                            disabled={updating}
                            className={`w-12 h-7 rounded-full transition-colors relative ${
                                stravaConnected ? 'bg-orange-500' : 'bg-gray-200'
                            } ${updating ? 'opacity-50' : ''}`}
                        >
                            <div className={`w-5 h-5 rounded-full bg-white shadow-sm transition-transform absolute top-1 ${
                                stravaConnected ? 'left-6' : 'left-1'
                            }`} />
                        </button>
                    </div>
                </div>

                {/* App info */}
                <div className="mt-6 text-center">
                    <p className="text-xs text-gray-400">Ayda Run v2.0</p>
                    <p className="text-xs text-gray-300 mt-1">Made with love in Almaty</p>
                </div>
            </div>
        </div>
    )
}
