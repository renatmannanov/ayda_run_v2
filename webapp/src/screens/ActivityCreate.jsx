import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation, useParams } from 'react-router-dom'
import {
    FormInput,
    FormTextarea,
    FormSelect,
    FormCheckbox,
    SportChips,
    Button
} from '../components'
import { DropdownPicker, ToggleButtons, GPXUploadPopup, SuccessPopup } from '../components/ui'
import {
    difficultyLevels,
    getDifficultyLabel
} from '../data/sample_data'
import { useCreateActivity, useUpdateActivity, useActivity, useActivityParticipants, useClubs, useGroups } from '../hooks'
import { tg } from '../api'

export default function ActivityCreate() {
    const { id } = useParams()
    const isEditMode = !!id

    const navigate = useNavigate()
    const location = useLocation()
    const context = location.state // May contain pre-selected club/group

    const { mutateAsync: createActivity, isPending: creating } = useCreateActivity()
    const { mutateAsync: updateActivity, isPending: updating } = useUpdateActivity()

    // Fetch existing activity in edit mode
    const { data: existingActivity, isLoading: loadingActivity } = useActivity(isEditMode ? id : null)
    const { data: participantsData } = useActivityParticipants(isEditMode ? id : null)
    const participants = participantsData || []

    const loading = creating || updating
    const { data: clubs = [] } = useClubs()
    const { data: allGroups = [] } = useGroups()

    // Form state
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

    // New unified visibility/access state
    const [visibility, setVisibility] = useState('public')
    const [access, setAccess] = useState('open')

    // Flow state for create mode
    const [flowStep, setFlowStep] = useState('form') // 'form' | 'gpx' | 'success'
    const [createdActivityId, setCreatedActivityId] = useState(null)
    const [shareLink, setShareLink] = useState('')

    const [showDifficultyPicker, setShowDifficultyPicker] = useState(false)
    const [errors, setErrors] = useState({})

    // Build visibility options
    const visibilityOptions = useMemo(() => {
        const options = [
            { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' }
        ]

        // Add clubs user is member of
        clubs.filter(c => c.isMember).forEach(club => {
            options.push({
                id: `club_${club.id}`,
                icon: '🏆',
                label: club.name,
                sublabel: 'клуб'
            })
        })

        // Add groups user is member of
        allGroups.filter(g => g.isMember).forEach(group => {
            options.push({
                id: `group_${group.id}`,
                icon: '👥',
                label: group.name,
                sublabel: group.clubName || 'группа'
            })
        })

        return options
    }, [clubs, allGroups])

    // Access options
    const accessOptions = [
        { id: 'open', label: 'Все желающие' },
        { id: 'request', icon: '🔒', label: 'По заявке' }
    ]

    const getAccessHint = () => {
        if (access === 'open') {
            return visibility === 'public'
                ? 'Любой может записаться на тренировку'
                : 'Любой участник может записаться'
        }
        return 'Нужно одобрение организатора'
    }

    // Parse visibility to club_id/group_id for API
    const parseVisibility = (vis) => {
        if (vis === 'public') {
            return { club_id: null, group_id: null }
        }
        if (vis.startsWith('club_')) {
            return { club_id: vis.replace('club_', ''), group_id: null }
        }
        if (vis.startsWith('group_')) {
            return { club_id: null, group_id: vis.replace('group_', '') }
        }
        return { club_id: null, group_id: null }
    }

    // Get visibility display for edit mode
    const getVisibilityDisplay = () => {
        const option = visibilityOptions.find(o => o.id === visibility)
        if (!option) return 'Публичная'
        return `${option.icon} ${option.label}`
    }

    // Fix for Telegram Desktop WebApp input focus bug
    useEffect(() => {
        if (document.activeElement) {
            document.activeElement.blur()
        }
        const timer = setTimeout(() => {
            if (document.activeElement) {
                document.activeElement.blur()
            }
        }, 100)
        return () => clearTimeout(timer)
    }, [])

    // Auto-populate visibility from context
    useEffect(() => {
        if (context?.groupId) {
            setVisibility(`group_${context.groupId}`)
        } else if (context?.clubId && context.clubId !== null) {
            setVisibility(`club_${context.clubId}`)
        }
    }, [context])

    // Populate form when editing existing activity
    useEffect(() => {
        if (existingActivity && isEditMode) {
            setTitle(existingActivity.title || '')
            setDescription(existingActivity.description || '')

            if (existingActivity.date) {
                const dateObj = new Date(existingActivity.date)
                setDate(dateObj.toISOString().split('T')[0])
                setTime(dateObj.toTimeString().slice(0, 5))
            }

            setLocationValue(existingActivity.location || '')
            setSportType(existingActivity.sportType || 'running')
            setDistance(existingActivity.distance?.toString() || '')
            setDuration(existingActivity.duration?.toString() || '')
            setDifficulty(existingActivity.difficulty || 'medium')

            if (existingActivity.maxParticipants === null) {
                setNoLimit(true)
                setMaxParticipants('20')
            } else {
                setNoLimit(false)
                setMaxParticipants(existingActivity.maxParticipants.toString())
            }

            setAccess(existingActivity.isOpen !== false ? 'open' : 'request')

            // Set visibility from existing activity
            if (existingActivity.groupId) {
                setVisibility(`group_${existingActivity.groupId}`)
            } else if (existingActivity.clubId) {
                setVisibility(`club_${existingActivity.clubId}`)
            } else {
                setVisibility('public')
            }
        }
    }, [existingActivity, isEditMode])

    const validate = () => {
        const newErrors = {}
        if (!title.trim()) newErrors.title = true
        if (!date) newErrors.date = true
        if (!locationValue.trim()) newErrors.location = true
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleSubmit = async () => {
        if (!validate()) return

        try {
            if (isEditMode) {
                // Update existing activity
                const payload = {
                    title,
                    date: `${date}T${time}:00`,
                    location: locationValue,
                    distance: distance ? parseFloat(distance) : null,
                    duration: duration ? parseInt(duration) : null,
                    difficulty,
                    max_participants: noLimit ? null : parseInt(maxParticipants),
                    description,
                    is_open: access === 'open'
                }

                const creatorId = String(existingActivity?.creatorId || '')
                const joinedCount = participants.filter(p =>
                    String(p.userId) !== creatorId &&
                    ['registered', 'confirmed'].includes(p.status)
                ).length

                const saveChanges = async (notifyParticipants) => {
                    await updateActivity({ id, data: payload, notifyParticipants })
                    tg.showAlert('Изменения сохранены!')
                    navigate(`/activity/${id}`)
                }

                if (joinedCount > 0) {
                    const word = joinedCount === 1 ? 'участник' :
                                joinedCount < 5 ? 'участника' : 'участников'

                    tg.showConfirm(
                        `У этой тренировки ${joinedCount} ${word}. Сохранить изменения и уведомить их?`,
                        (confirmed) => {
                            if (confirmed) saveChanges(true)
                        }
                    )
                } else {
                    await saveChanges(false)
                }
            } else {
                // Create new activity
                const { club_id, group_id } = parseVisibility(visibility)

                const result = await createActivity({
                    title,
                    date: `${date}T${time}:00`,
                    location: locationValue,
                    sport_type: sportType,
                    distance: distance ? parseFloat(distance) : null,
                    duration: duration ? parseInt(duration) : null,
                    difficulty,
                    max_participants: noLimit ? null : parseInt(maxParticipants),
                    description,
                    club_id,
                    group_id,
                    is_open: access === 'open'
                })

                if (!result?.id) {
                    throw new Error('Не удалось создать активность')
                }

                setCreatedActivityId(result.id)
                setShareLink(`https://t.me/aydarun_bot?start=activity_${result.id}`)
                setFlowStep('gpx')
            }
        } catch (e) {
            console.error('Failed to save activity', e)
            tg.showAlert(`Ошибка: ${e.message || 'Не удалось сохранить'}`)
        }
    }

    const handleGpxUpload = () => {
        setFlowStep('success')
    }

    const handleGpxSkip = () => {
        setFlowStep('success')
    }

    // Copy link
    const handleCopyLink = () => {
        navigator.clipboard.writeText(shareLink)
        tg.showAlert('Ссылка скопирована!')
    }

    // Share via Telegram
    const handleShare = () => {
        if (tg.webApp?.openTelegramLink) {
            const text = encodeURIComponent(`Присоединяйся к активности "${title}"!`)
            tg.webApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${text}`)
        } else {
            navigator.clipboard.writeText(shareLink)
            tg.showAlert('Ссылка скопирована!')
        }
    }

    const handleSuccessDone = () => {
        navigate(`/activity/${createdActivityId}`)
    }

    // Difficulty Picker
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
                        className={`w-full text-left py-3 px-2 rounded-lg transition-colors ${
                            difficulty === level.id ? 'bg-gray-100' : 'hover:bg-gray-50'
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
                <span className="text-base font-medium text-gray-800">
                    {isEditMode ? 'Редактирование' : 'Новая тренировка'}
                </span>
                <div className="w-16" />
            </div>

            {/* Loading state for edit mode */}
            {isEditMode && loadingActivity && (
                <div className="flex-1 flex items-center justify-center">
                    <span className="text-gray-500">Загрузка...</span>
                </div>
            )}

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
                            className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 outline-none transition-colors ${
                                errors.date ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
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

                {/* Sport type - disabled in edit mode */}
                {isEditMode ? (
                    <div className="mb-4">
                        <label className="text-sm text-gray-700 mb-2 block">Тип активности</label>
                        <div className="px-4 py-3 bg-gray-100 rounded-xl text-sm text-gray-500">
                            {sportType === 'running' && '🏃 Бег'}
                            {sportType === 'trail' && '🏔️ Трейл'}
                            {sportType === 'cycling' && '🚴 Вело'}
                            {sportType === 'hiking' && '🥾 Хайкинг'}
                            {sportType === 'other' && '⚡ Другое'}
                            <span className="text-xs text-gray-400 ml-2">(нельзя изменить)</span>
                        </div>
                    </div>
                ) : (
                    <SportChips
                        selected={sportType}
                        onChange={setSportType}
                        multiple={false}
                    />
                )}

                <div className="border-t border-gray-200 my-4" />

                {/* Stats row - hide distance/elevation for yoga and workout */}
                {!['yoga', 'workout'].includes(sportType) && (
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
                )}

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
                            className={`w-24 px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400 transition-colors ${
                                noLimit ? 'bg-gray-50 text-gray-400' : ''
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

                {/* Visibility */}
                {isEditMode ? (
                    <div className="mb-4">
                        <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
                        <div className="px-4 py-3 bg-gray-100 rounded-xl text-sm text-gray-500">
                            {getVisibilityDisplay()}
                            <span className="text-xs text-gray-400 ml-2">(нельзя изменить)</span>
                        </div>
                    </div>
                ) : (
                    <div className="mb-4">
                        <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
                        <DropdownPicker
                            value={visibility}
                            options={visibilityOptions}
                            onChange={setVisibility}
                            placeholder="Выбрать..."
                        />
                    </div>
                )}

                {/* Access */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Кто может записаться?</label>
                    <ToggleButtons
                        options={accessOptions}
                        selected={access}
                        onChange={setAccess}
                        hint={getAccessHint()}
                    />
                </div>
            </div>

            {/* Submit button */}
            <div className="px-4 pb-6 pt-2 border-t border-gray-200">
                <Button
                    onClick={handleSubmit}
                    loading={loading}
                    disabled={isEditMode && loadingActivity}
                >
                    {isEditMode ? 'Сохранить изменения' : 'Создать активность'}
                </Button>
            </div>

            {/* Pickers */}
            {showDifficultyPicker && <DifficultyPicker />}

            {/* GPX Upload Popup (create mode only) */}
            <GPXUploadPopup
                isOpen={flowStep === 'gpx'}
                onClose={() => setFlowStep('form')}
                onSkip={handleGpxSkip}
                onUpload={handleGpxUpload}
                mode="create"
                activityId={createdActivityId}
            />

            {/* Success Popup */}
            <SuccessPopup
                isOpen={flowStep === 'success'}
                title="Активность создана!"
                description="Пригласи участников по ссылке"
                shareLink={shareLink}
                onCopyLink={handleCopyLink}
                onShare={handleShare}
                onDone={handleSuccessDone}
                doneButtonText="Перейти к активности →"
            />
        </div>
    )
}
