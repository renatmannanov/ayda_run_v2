import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
    FormInput,
    FormTextarea,
    FormSelect,
    FormCheckbox,
    SportChips,
    Button
} from '../components'
import {
    difficultyLevels,
    getDifficultyLabel
} from '../data/sample_data'
import { useCreateActivity, useClubs, useGroups } from '../hooks'

export default function ActivityCreate() {
    const navigate = useNavigate()
    const location = useLocation()
    const context = location.state // May contain pre-selected club/group

    // Debug: log context to see what's passed
    console.log('🎯 ActivityCreate context:', context)

    const { mutate: createActivity, loading } = useCreateActivity()
    const { data: clubs = [] } = useClubs()
    // Fetch a flat list of all groups, or fetch lazily.
    // Let's assume useGroups() fetches all visible groups or user groups.
    // Better to fetch all user's groups or just fetch all if list is small.
    // For now let's use useGroups() w/o filter to get all, filter client side for picker.
    const { data: allGroups = [] } = useGroups()

    // Form state
    // ... (keeping state as before but integrating API submission)
    const [title, setTitle] = useState('')
    const [date, setDate] = useState('')
    const [time, setTime] = useState('07:00')
    const [locationValue, setLocationValue] = useState('')
    const [sportType, setSportType] = useState('running')
    const [distance, setDistance] = useState('')
    const [elevation, setElevation] = useState('')
    const [duration, setDuration] = useState('')
    const [difficulty, setDifficulty] = useState('medium')
    const [maxParticipants, setMaxParticipants] = useState('20')
    const [noLimit, setNoLimit] = useState(false)
    const [description, setDescription] = useState('')
    const [selectedClub, setSelectedClub] = useState(
        (context?.clubId && context.clubId !== null) ? context.clubId.toString() : ''
    )
    const [selectedGroup, setSelectedGroup] = useState(
        (context?.groupId && context.groupId !== null) ? context.groupId.toString() : ''
    )
    const [isPublic, setIsPublic] = useState(false)
    const [isOpen, setIsOpen] = useState(true) // true = anyone can join, false = by request only

    const [showDifficultyPicker, setShowDifficultyPicker] = useState(false)
    const [showClubPicker, setShowClubPicker] = useState(false)
    const [errors, setErrors] = useState({})

    // Fix for Telegram Desktop WebApp input focus bug
    useEffect(() => {
        // Remove any stuck focus
        if (document.activeElement) {
            document.activeElement.blur()
        }
        // Small delay to ensure Telegram WebApp is ready
        const timer = setTimeout(() => {
            if (document.activeElement) {
                document.activeElement.blur()
            }
        }, 100)
        return () => clearTimeout(timer)
    }, [])

    // Auto-populate group/club from context
    useEffect(() => {
        if (context?.groupId) {
            setSelectedGroup(context.groupId.toString())
        }
        if (context?.clubId && context.clubId !== null) {
            setSelectedClub(context.clubId.toString())
        }
    }, [context])

    const validate = () => {
        const newErrors = {}
        if (!title.trim()) newErrors.title = true
        if (!date) newErrors.date = true
        if (!locationValue.trim()) newErrors.location = true
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async () => {
        if (validate()) {
            try {
                await createActivity({
                    title,
                    date: `${date}T${time}:00`, // ISO format
                    location: locationValue,
                    sport_type: sportType,
                    distance: distance ? parseFloat(distance) : null,
                    duration: duration ? parseInt(duration) : null,
                    difficulty,
                    max_participants: noLimit ? null : parseInt(maxParticipants),
                    description,
                    club_id: isPublic || !selectedClub ? null : selectedClub,
                    group_id: isPublic || !selectedGroup ? null : selectedGroup,
                    is_open: isOpen
                })

                alert('Тренировка создана!')
                navigate('/')
            } catch (e) {
                console.error('Failed to create activity', e)
                // Покажем детальную ошибку от бэкенда если есть
                alert(`Ошибка: ${JSON.stringify(e.message || e)}`)
            }
        }
    }

    // Get selected club object
    const getSelectedClubObj = () => {
        return clubs.find(c => c.id.toString() === selectedClub)
    }

    // Format club/group display
    const getClubGroupDisplay = () => {
        if (isPublic) return 'Публичная (видят все)'

        // Standalone group (no club)
        if (selectedGroup && !selectedClub) {
            const group = allGroups.find(g => g.id.toString() === selectedGroup)
            return group ? `👥 ${group.name}` : null
        }

        // Club or club group
        if (!selectedClub) return null
        const club = getSelectedClubObj()
        if (!club) return null
        if (selectedGroup) {
            const group = allGroups.find(g => g.id.toString() === selectedGroup)
            return `${club.name} / ${group?.name || ''}`
        }
        return club.name
    }

    // Get all groups (no filtering by selectedClub)
    const getAllGroups = () => {
        return allGroups
    }

    // ... (Pickers UI same as before, updated data source from hooks) ...
    const DifficultyPicker = () => (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={() => setShowDifficultyPicker(false)}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl p-6"
                onClick={e => e.stopPropagation()}
            >
                <h3 className="text-base font-medium text-gray-800 mb-4">Сложность</h3>
                {difficultyLevels.map(level => (
                    <button
                        key={level.id}
                        onClick={() => {
                            setDifficulty(level.id)
                            setShowDifficultyPicker(false)
                        }}
                        className={`w-full text-left py-3 px-2 rounded-lg transition-colors ${difficulty === level.id ? 'bg-gray-100' : 'hover:bg-gray-50'
                            }`}
                    >
                        <span className="text-sm text-gray-700">{level.label}</span>
                    </button>
                ))}
                <button
                    onClick={() => setShowDifficultyPicker(false)}
                    className="w-full mt-4 py-3 text-gray-400 text-sm"
                >
                    Отмена
                </button>
            </div>
        </div>
    )

    const ClubGroupPicker = () => (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={() => setShowClubPicker(false)}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl p-6 max-h-[70vh] overflow-auto"
                onClick={e => e.stopPropagation()}
            >
                <h3 className="text-base font-medium text-gray-800 mb-4">Клуб / Группа</h3>

                {/* Public option */}
                <button
                    onClick={() => {
                        setIsPublic(true)
                        setSelectedClub('')
                        setSelectedGroup('')
                        setShowClubPicker(false)
                    }}
                    className={`w-full text-left py-3 px-2 rounded-lg mb-2 transition-colors ${isPublic ? 'bg-gray-100' : 'hover:bg-gray-50'
                        }`}
                >
                    <span className="text-sm text-gray-700">🌍 Публичная (видят все)</span>
                </button>

                <div className="border-t border-gray-200 my-3" />

                {/* Clubs */}
                {clubs.filter(c => c.isMember).map(club => (
                    <button
                        key={club.id}
                        onClick={() => {
                            setIsPublic(false)
                            setSelectedClub(club.id.toString())
                            setSelectedGroup('')
                            setShowClubPicker(false)
                        }}
                        className={`w-full text-left py-3 px-2 rounded-lg mb-2 transition-colors ${selectedClub === club.id.toString() && !selectedGroup ? 'bg-gray-100' : 'hover:bg-gray-50'
                            }`}
                    >
                        <span className="text-sm text-gray-700">🏆 {club.name}</span>
                    </button>
                ))}

                {/* Groups within clubs */}
                {getAllGroups().filter(g => g.clubId && g.isMember).map(group => (
                    <button
                        key={group.id}
                        onClick={() => {
                            setIsPublic(false)
                            setSelectedClub(group.clubId.toString())
                            setSelectedGroup(group.id.toString())
                            setShowClubPicker(false)
                        }}
                        className={`w-full text-left py-3 px-2 rounded-lg mb-2 transition-colors ${selectedGroup === group.id.toString() ? 'bg-gray-100' : 'hover:bg-gray-50'
                            }`}
                    >
                        <span className="text-sm text-gray-600">→ {group.name}</span>
                    </button>
                ))}

                {/* Independent Groups (clubId === null) */}
                {getAllGroups().filter(g => !g.clubId && g.isMember).map(group => (
                    <button
                        key={group.id}
                        onClick={() => {
                            setIsPublic(false)
                            setSelectedClub('')
                            setSelectedGroup(group.id.toString())
                            setShowClubPicker(false)
                        }}
                        className={`w-full text-left py-3 px-2 rounded-lg mb-2 transition-colors ${selectedGroup === group.id.toString() ? 'bg-gray-100' : 'hover:bg-gray-50'
                            }`}
                    >
                        <span className="text-sm text-gray-700">👥 {group.name}</span>
                    </button>
                ))}

                <button
                    onClick={() => setShowClubPicker(false)}
                    className="w-full mt-4 py-3 text-gray-400 text-sm"
                >
                    Отмена
                </button>
            </div>
        </div>
    )

    return (
        <div className="min-h-screen bg-white flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
                <button
                    onClick={() => navigate(-1)}
                    className="text-gray-500 text-sm hover:text-gray-700"
                >
                    ✕ Отмена
                </button>
                <span className="text-base font-medium text-gray-800">Новая тренировка</span>
                <div className="w-16" />
            </div>

            {/* Form */}
            <div className="flex-1 overflow-auto px-4 py-4">
                <FormInput
                    label="Название"
                    value={title}
                    onChange={setTitle}
                    placeholder="Утренняя пробежка"
                    error={errors.title}
                    required
                />

                {/* Date & Time */}
                <div className="flex gap-3 mb-4">
                    <div className="flex-1">
                        <label className="text-sm text-gray-700 mb-2 block">
                            Когда <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="date"
                            value={date}
                            min={new Date().toISOString().split('T')[0]}
                            onChange={(e) => setDate(e.target.value)}
                            className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 outline-none transition-colors ${errors.date ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
                                }`}
                        />
                    </div>
                    <div className="w-28">
                        <label className="text-sm text-gray-700 mb-2 block">&nbsp;</label>
                        <input
                            type="time"
                            value={time}
                            onChange={(e) => setTime(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400 transition-colors"
                        />
                    </div>
                </div>

                <FormInput
                    label="Где"
                    value={locationValue}
                    onChange={setLocationValue}
                    placeholder="Центральный парк, фонтан"
                    error={errors.location}
                    required
                />

                <SportChips
                    selected={sportType}
                    onChange={setSportType}
                    multiple={false}
                />

                <div className="border-t border-gray-200 my-4" />

                {/* Stats row */}
                <div className="flex gap-3 mb-4">
                    <div className="flex-1">
                        <FormInput
                            label="Дистанция"
                            value={distance}
                            onChange={setDistance}
                            placeholder="10"
                            type="number"
                            suffix="км"
                        />
                    </div>
                    <div className="flex-1">
                        <FormInput
                            label="Набор"
                            value={elevation}
                            onChange={setElevation}
                            placeholder="150"
                            type="number"
                            suffix="м"
                        />
                    </div>
                </div>

                <div className="flex gap-3 mb-4">
                    <div className="flex-1">
                        <FormInput
                            label="Длительность (мин)"
                            value={duration}
                            onChange={setDuration}
                            placeholder="60"
                            type="number"
                        />
                    </div>
                    <div className="flex-1">
                        <FormSelect
                            label="Сложность"
                            value={getDifficultyLabel(difficulty)}
                            onClick={() => setShowDifficultyPicker(true)}
                        />
                    </div>
                </div>

                {/* Max participants */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Макс. участников</label>
                    <div className="flex items-center gap-3">
                        <input
                            type="number"
                            value={maxParticipants}
                            onChange={(e) => setMaxParticipants(e.target.value)}
                            disabled={noLimit}
                            className={`w-24 px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400 transition-colors ${noLimit ? 'bg-gray-50 text-gray-400' : ''
                                }`}
                        />
                        <FormCheckbox
                            label="Без лимита"
                            checked={noLimit}
                            onChange={setNoLimit}
                        />
                    </div>
                </div>

                <div className="border-t border-gray-200 my-4" />

                <FormTextarea
                    label="Описание"
                    value={description}
                    onChange={setDescription}
                    placeholder="Разминка у фонтана, потом 2 круга по парку. Берите воду!"
                    rows={4}
                />

                <div className="border-t border-gray-200 my-4" />

                {/* Club/Group selector */}
                <FormSelect
                    label="Клуб / Группа"
                    value={getClubGroupDisplay()}
                    onClick={() => setShowClubPicker(true)}
                />

                <div className="border-t border-gray-200 my-4" />

                {/* Access control */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Кто может записаться?</label>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setIsOpen(true)}
                            className={`flex-1 py-3 px-4 rounded-xl text-sm border transition-colors ${
                                isOpen
                                    ? 'border-gray-800 bg-gray-800 text-white'
                                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                            }`}
                        >
                            Все желающие
                        </button>
                        <button
                            onClick={() => setIsOpen(false)}
                            className={`flex-1 py-3 px-4 rounded-xl text-sm border transition-colors ${
                                !isOpen
                                    ? 'border-gray-800 bg-gray-800 text-white'
                                    : 'border-gray-200 text-gray-600 hover:border-gray-300'
                            }`}
                        >
                            🔒 По заявке
                        </button>
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                        {isOpen
                            ? 'Любой может записаться на тренировку'
                            : 'Участники отправляют заявку, вы одобряете'}
                    </p>
                </div>
            </div>

            {/* Submit button */}
            <div className="px-4 pb-6 pt-2 border-t border-gray-200">
                <Button
                    onClick={handleSubmit}
                    loading={loading}
                >
                    Создать тренировку
                </Button>
            </div>

            {/* Pickers */}
            {showDifficultyPicker && <DifficultyPicker />}
            {showClubPicker && <ClubGroupPicker />}
        </div>
    )
}
