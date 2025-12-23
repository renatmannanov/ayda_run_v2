import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '../api'
import { Avatar, ProgressBar, LoadingScreen, ErrorScreen } from '../components/ui'

const PERIODS = [
    { id: 'month', label: 'Месяц' },
    { id: 'quarter', label: 'Квартал' },
    { id: 'year', label: 'Год' },
    { id: 'all', label: 'Всё время' },
]

export default function Statistics() {
    const navigate = useNavigate()
    const [period, setPeriod] = useState('month')
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // Fetch stats when period changes
    useEffect(() => {
        const fetchStats = async () => {
            setLoading(true)
            setError(null)
            try {
                const data = await usersApi.getStats(period)
                setStats(data)
            } catch (err) {
                console.error('Failed to fetch stats:', err)
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }
        fetchStats()
    }, [period])

    if (loading && !stats) {
        return <LoadingScreen text="Загружаем статистику..." />
    }

    if (error && !stats) {
        return <ErrorScreen message={error} onRetry={() => setPeriod(period)} />
    }

    const totalSports = stats?.sports?.reduce((sum, s) => sum + s.count, 0) || 0

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
                <h1 className="text-base font-medium text-gray-800">Статистика</h1>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-8">
                {/* Period Tabs */}
                <div className="bg-white rounded-2xl p-4">
                    <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
                        {PERIODS.map(p => (
                            <button
                                key={p.id}
                                onClick={() => setPeriod(p.id)}
                                className={`flex-1 py-1.5 px-2 text-xs font-medium rounded-md transition-colors ${
                                    period === p.id
                                        ? 'bg-white text-gray-800 shadow-sm'
                                        : 'text-gray-500 hover:text-gray-700'
                                }`}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Loading overlay */}
                {loading && (
                    <div className="flex justify-center py-4">
                        <div className="w-6 h-6 border-2 border-gray-200 border-t-gray-800 rounded-full animate-spin" />
                    </div>
                )}

                {/* Registered / Attended */}
                {!loading && stats && (
                    <>
                        <div className="bg-white rounded-2xl p-4">
                            <h3 className="text-sm font-medium text-gray-800 mb-3">
                                Записался / Участвовал
                            </h3>
                            <div className="flex items-baseline justify-between mb-2">
                                <span className="text-2xl font-medium text-gray-800">
                                    {stats.attended}
                                    <span className="text-gray-300"> / </span>
                                    {stats.registered}
                                </span>
                                <span className="text-sm text-gray-400">
                                    {stats.attendance_rate}%
                                </span>
                            </div>
                            <ProgressBar
                                value={stats.attended}
                                max={stats.registered || 1}
                                showPercent={false}
                            />
                        </div>

                        {/* By Clubs & Groups */}
                        {stats.clubs?.length > 0 && (
                            <div className="bg-white rounded-2xl p-4">
                                <h3 className="text-sm font-medium text-gray-800 mb-3">
                                    По клубам и группам
                                </h3>
                                <div className="space-y-3">
                                    {stats.clubs.map((club) => (
                                        <div key={club.id} className="flex items-center gap-3">
                                            <Avatar
                                                src={club.avatar}
                                                name={club.name}
                                                size="sm"
                                                forcePhoto
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-baseline justify-between mb-1">
                                                    <span className="text-sm text-gray-700 truncate">
                                                        {club.name}
                                                    </span>
                                                    <span className="text-xs text-gray-400 ml-2 flex-shrink-0">
                                                        {club.attended}/{club.registered}
                                                    </span>
                                                </div>
                                                <ProgressBar
                                                    value={club.attended}
                                                    max={club.registered || 1}
                                                    showPercent={false}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* By Sports */}
                        {stats.sports?.length > 0 && (
                            <div className="bg-white rounded-2xl p-4">
                                <h3 className="text-sm font-medium text-gray-800 mb-3">
                                    По видам спорта
                                </h3>
                                <div className="space-y-3">
                                    {stats.sports.map((sport) => (
                                        <div key={sport.id}>
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-sm text-gray-700">
                                                    {sport.icon} {sport.name}
                                                </span>
                                                <span className="text-xs text-gray-400">
                                                    {sport.count}
                                                </span>
                                            </div>
                                            <ProgressBar
                                                value={sport.count}
                                                max={totalSports || 1}
                                                showPercent={false}
                                            />
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Empty state */}
                        {stats.registered === 0 && (
                            <div className="bg-white rounded-2xl p-6 text-center">
                                <span className="text-4xl block mb-3">📊</span>
                                <p className="text-sm text-gray-500">
                                    Пока нет статистики за этот период
                                </p>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
