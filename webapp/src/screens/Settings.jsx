import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../contexts/UserContext'
import { LoadingScreen } from '../components/ui'

export default function Settings() {
    const navigate = useNavigate()
    const {
        user,
        isLoading,
        showPhoto,
        updating,
        updateShowPhoto,
        updateStravaLink,
        removeStravaLink
    } = useUser()

    const [stravaInput, setStravaInput] = useState('')
    const [showStravaInput, setShowStravaInput] = useState(false)
    const [savingStrava, setSavingStrava] = useState(false)

    if (isLoading) {
        return <LoadingScreen text="Загружаем настройки..." />
    }

    const handleTogglePhoto = async () => {
        await updateShowPhoto(!showPhoto)
    }

    const handleAddStrava = async () => {
        if (!stravaInput.trim()) return
        setSavingStrava(true)
        const success = await updateStravaLink(stravaInput.trim())
        setSavingStrava(false)
        if (success) {
            setShowStravaInput(false)
            setStravaInput('')
        }
    }

    const handleRemoveStrava = async () => {
        setSavingStrava(true)
        await removeStravaLink()
        setSavingStrava(false)
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

                {/* Strava */}
                <div className="bg-white rounded-2xl p-4">
                    <h3 className="text-sm font-medium text-gray-800 mb-3">Strava</h3>

                    {user?.stravaLink ? (
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 min-w-0">
                                <span className="w-6 h-6 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">
                                    S
                                </span>
                                <span className="text-sm text-gray-600 truncate">
                                    {user.stravaLink.replace(/^https?:\/\//, '')}
                                </span>
                            </div>
                            <button
                                onClick={handleRemoveStrava}
                                disabled={savingStrava}
                                className="text-xs text-red-500 hover:text-red-600 flex-shrink-0 ml-2"
                            >
                                {savingStrava ? 'Удаление...' : 'Отвязать'}
                            </button>
                        </div>
                    ) : showStravaInput ? (
                        <div className="space-y-3">
                            <input
                                type="text"
                                value={stravaInput}
                                onChange={(e) => setStravaInput(e.target.value)}
                                placeholder="strava.com/athletes/..."
                                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-gray-400"
                                autoFocus
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={() => {
                                        setShowStravaInput(false)
                                        setStravaInput('')
                                    }}
                                    disabled={savingStrava}
                                    className="flex-1 py-2 text-sm text-gray-600 hover:text-gray-800"
                                >
                                    Отмена
                                </button>
                                <button
                                    onClick={handleAddStrava}
                                    disabled={savingStrava || !stravaInput.trim()}
                                    className="flex-1 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                                >
                                    {savingStrava ? 'Сохранение...' : 'Сохранить'}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button
                            onClick={() => setShowStravaInput(true)}
                            className="w-full py-3 bg-orange-500 text-white rounded-xl text-sm font-medium hover:bg-orange-600 transition-colors flex items-center justify-center gap-2"
                        >
                            <span className="font-bold">S</span>
                            <span>Добавить ссылку на Strava</span>
                        </button>
                    )}
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
