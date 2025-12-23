import React, { useState, useMemo } from 'react'
import { Avatar } from './ui'
import { SPORT_TYPES } from '../constants/sports'

/**
 * AttendancePopup - Popup for organizers to mark participant attendance
 *
 * Shows list of participants with checkboxes to mark attendance.
 * Supports adding members from club/group who didn't register.
 *
 * Attendance states cycle: null -> true (attended) -> false (missed) -> null
 */
export default function AttendancePopup({
    isOpen,
    onClose,
    participants = [],
    clubMembers = [], // Members from club/group who didn't register
    onToggleAttendance,
    onAddParticipant,
    onSave,
    saving = false
}) {
    const [showAddMember, setShowAddMember] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')

    // Filter available members (not already participants)
    // Note: All hooks MUST be called before any early return
    const availableMembers = useMemo(() => {
        const participantIds = new Set(participants.map(p => p.userId || p.id))
        return clubMembers
            .filter(m => !participantIds.has(m.userId || m.id))
            .filter(m => {
                if (!searchQuery) return true
                const name = m.name || m.firstName || ''
                return name.toLowerCase().includes(searchQuery.toLowerCase())
            })
    }, [clubMembers, participants, searchQuery])

    // Early return AFTER all hooks
    if (!isOpen) return null

    // Count attended
    const attendedCount = participants.filter(p => p.attended === true).length
    const totalCount = participants.length

    // Helper to parse and get sport icons
    const getSportIcons = (preferredSports) => {
        try {
            if (!preferredSports) return []
            const sports = typeof preferredSports === 'string'
                ? JSON.parse(preferredSports)
                : preferredSports
            return sports.map(sportId => {
                const sport = SPORT_TYPES.find(s => s.id === sportId)
                return sport?.icon || null
            }).filter(Boolean)
        } catch {
            return []
        }
    }

    const handleSave = () => {
        if (onSave) onSave()
        onClose()
    }

    return (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex flex-col justify-end"
            onClick={onClose}
        >
            <div
                className="bg-white w-full max-w-md mx-auto rounded-t-2xl flex flex-col"
                onClick={e => e.stopPropagation()}
                style={{ maxHeight: '70vh' }}
            >
                {/* Header */}
                <div className="px-4 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-base font-medium text-gray-800">
                            Отметка посещения
                        </span>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 text-xl"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Progress bar */}
                    <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-green-500 transition-all duration-300"
                                style={{ width: `${totalCount > 0 ? (attendedCount / totalCount) * 100 : 0}%` }}
                            />
                        </div>
                        <span className="text-sm text-gray-500 font-medium">
                            {attendedCount}/{totalCount}
                        </span>
                    </div>
                </div>

                {/* Participants List */}
                <div className="flex-1 overflow-auto px-4 py-2">
                    {participants.map(p => {
                        const sportIcons = getSportIcons(p.preferredSports)
                        return (
                            <div
                                key={p.id || p.userId}
                                className="flex items-center py-3 border-b border-gray-100 last:border-0"
                            >
                                {/* Avatar */}
                                <Avatar
                                    src={p.photo}
                                    name={p.name || p.firstName}
                                    size="md"
                                    className="mr-3 flex-shrink-0"
                                />

                                {/* Name + Sports */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm text-gray-700">
                                            {p.name || p.firstName}
                                        </span>
                                        {p.isOrganizer && (
                                            <span className="text-xs text-gray-400">Орг</span>
                                        )}
                                        {sportIcons.length > 0 && (
                                            <div className="flex gap-0.5">
                                                {sportIcons.slice(0, 3).map((icon, idx) => (
                                                    <span key={idx} className="text-sm">{icon}</span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Attendance checkbox - big tap area */}
                                <button
                                    onClick={() => onToggleAttendance(p.userId || p.id)}
                                    className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all ${
                                        p.attended === true
                                            ? 'border-green-500 bg-green-500 text-white'
                                            : p.attended === false
                                            ? 'border-gray-300 bg-gray-100 text-gray-400'
                                            : 'border-gray-300 text-gray-300 hover:border-gray-400'
                                    }`}
                                >
                                    {p.attended === true ? (
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : p.attended === false ? (
                                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    ) : null}
                                </button>
                            </div>
                        )
                    })}
                </div>

                {/* Add member section */}
                {clubMembers.length > 0 && (
                    <div className="border-t border-gray-200">
                        {!showAddMember ? (
                            <button
                                onClick={() => setShowAddMember(true)}
                                className="w-full px-4 py-4 text-left text-sm text-gray-500 hover:bg-gray-50 flex items-center gap-2"
                            >
                                <span className="text-lg">+</span>
                                <span>Добавить участника</span>
                            </button>
                        ) : (
                            <div className="p-4">
                                <div className="flex items-center gap-2 mb-3">
                                    <input
                                        type="text"
                                        placeholder="Поиск по имени..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-gray-400"
                                        autoFocus
                                    />
                                    <button
                                        onClick={() => { setShowAddMember(false); setSearchQuery(''); }}
                                        className="text-gray-400 hover:text-gray-600 px-2"
                                    >
                                        ✕
                                    </button>
                                </div>

                                {/* Available members list */}
                                <div className="max-h-32 overflow-auto">
                                    {availableMembers.length === 0 ? (
                                        <p className="text-sm text-gray-400 text-center py-2">
                                            {searchQuery ? 'Никого не найдено' : 'Все участники уже добавлены'}
                                        </p>
                                    ) : (
                                        availableMembers.map(m => (
                                            <button
                                                key={m.userId || m.id}
                                                onClick={() => {
                                                    onAddParticipant(m)
                                                    setSearchQuery('')
                                                }}
                                                className="w-full flex items-center gap-3 py-2 hover:bg-gray-50 rounded-lg px-2"
                                            >
                                                <Avatar
                                                    src={m.photo}
                                                    name={m.name || m.firstName}
                                                    size="sm"
                                                />
                                                <span className="text-sm text-gray-700">
                                                    {m.name || m.firstName}
                                                </span>
                                                <span className="text-xs text-gray-400 ml-auto">
                                                    + добавить
                                                </span>
                                            </button>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Save button */}
                <div className="px-4 py-4 border-t border-gray-200">
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors disabled:opacity-50"
                    >
                        {saving ? 'Сохранение...' : 'Сохранить'}
                    </button>
                </div>
            </div>
        </div>
    )
}
