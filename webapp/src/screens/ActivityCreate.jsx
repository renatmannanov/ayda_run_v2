import React, { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation, useParams, useSearchParams } from 'react-router-dom'
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
import { useCreateRecurringSeries, useUpdateRecurring } from '../hooks/useRecurring'
import { tg, configApi } from '../api'
import { useToast } from '../contexts/ToastContext'
import { formatDateTimeForAPI, getLocalDateString, getLocalTimeString } from '../utils/timezone'

export default function ActivityCreate() {
    const { id } = useParams()
    const [searchParams] = useSearchParams()
    const isEditMode = !!id

    // Get scope from URL params (for recurring activity edits)
    const recurringScope = searchParams.get('scope') // 'this_only' | 'this_and_following'

    const navigate = useNavigate()
    const location = useLocation()
    const { showToast } = useToast()
    const context = location.state // May contain pre-selected club/group

    const { mutateAsync: createActivity, isPending: creating } = useCreateActivity()
    const { mutateAsync: updateActivity, isPending: updating } = useUpdateActivity()
    const { mutateAsync: updateRecurring, isPending: updatingRecurring } = useUpdateRecurring()
    const { mutateAsync: createRecurringSeries, isPending: creatingRecurring } = useCreateRecurringSeries()

    // Fetch existing activity in edit mode
    const { data: existingActivity, isLoading: loadingActivity } = useActivity(isEditMode ? id : null)
    const { data: participantsData } = useActivityParticipants(isEditMode ? id : null)
    const participants = participantsData || []

    const loading = creating || updating || updatingRecurring || creatingRecurring
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

    // Recurring state
    const [isRecurring, setIsRecurring] = useState(false)
    const [recurrenceFrequency, setRecurrenceFrequency] = useState(4) // 1-4 times per month
    const [recurrenceCount, setRecurrenceCount] = useState(12) // 1-12 occurrences

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

    // Check if user can create recurring activities (is organizer of selected club/group)
    const canCreateRecurring = useMemo(() => {
        if (visibility === 'public') return false

        if (visibility.startsWith('club_')) {
            const clubId = visibility.replace('club_', '')
            const club = clubs.find(c => String(c.id) === clubId)
            return club?.isAdmin === true
        }

        if (visibility.startsWith('group_')) {
            const groupId = visibility.replace('group_', '')
            const group = allGroups.find(g => String(g.id) === groupId)
            return group?.isAdmin === true
        }

        return false
    }, [visibility, clubs, allGroups])

    // Recurring frequency options (times per week)
    const frequencyOptions = [
        { id: 4, label: 'Каждую неделю' },
        { id: 2, label: 'Раз в 2 недели' },
        { id: 1, label: 'Раз в месяц' }
    ]

    // Get day of week from selected date (0=Mon, 6=Sun)
    const getDayOfWeekFromDate = (dateStr) => {
        if (!dateStr) return null
        const d = new Date(dateStr)
        // JS: 0=Sun, 1=Mon... -> convert to 0=Mon, 6=Sun
        const jsDay = d.getDay()
        return jsDay === 0 ? 6 : jsDay - 1
    }

    // Day names for display
    const dayNamesLong = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']

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
                setDate(getLocalDateString(dateObj))
                setTime(getLocalTimeString(dateObj))
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

        if (Object.keys(newErrors).length > 0) {
            // Show toast with error message
            showToast('Заполните обязательные поля', 'error')

            // Scroll to first error field
            const firstErrorField = Object.keys(newErrors)[0]
            const fieldElement = document.querySelector(`[data-field="${firstErrorField}"]`)
            if (fieldElement) {
                fieldElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
            return false
        }
        return true
    }

    const handleSubmit = async () => {
        if (!validate()) return

        try {
            if (isEditMode) {
                // Update existing activity
                const payload = {
                    title,
                    date: formatDateTimeForAPI(date, time),
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

                // Check if this is a recurring activity with scope
                const isRecurringEdit = existingActivity?.isRecurring && recurringScope

                const saveChanges = async (notifyParticipants) => {
                    if (isRecurringEdit) {
                        // Use recurring API for recurring activity edits
                        await updateRecurring({
                            activityId: id,
                            scope: recurringScope,
                            data: payload
                        })
                        const scopeText = recurringScope === 'this_and_following'
                            ? 'Эта и следующие тренировки обновлены'
                            : 'Тренировка обновлена'
                        showToast(scopeText)
                    } else {
                        // Regular activity update
                        await updateActivity({ id, data: payload, notifyParticipants })
                        showToast('Изменения сохранены')
                    }
                    navigate(`/activity/${id}`)
                }

                if (joinedCount > 0 && !isRecurringEdit) {
                    // Only ask for notification confirmation for non-recurring edits
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

                // Check if recurring
                if (isRecurring && canCreateRecurring) {
                    // Get day of week from selected date
                    const dayOfWeek = getDayOfWeekFromDate(date)

                    // Create recurring series
                    const result = await createRecurringSeries({
                        title,
                        description,
                        day_of_week: dayOfWeek,
                        time_of_day: time,
                        start_date: formatDateTimeForAPI(date, time),
                        frequency: recurrenceFrequency,
                        total_occurrences: recurrenceCount,
                        location: locationValue,
                        sport_type: sportType,
                        difficulty,
                        distance: distance ? parseFloat(distance) : null,
                        duration: duration ? parseInt(duration) : null,
                        max_participants: noLimit ? null : parseInt(maxParticipants),
                        club_id,
                        group_id
                    })

                    if (!result?.first_activity_id) {
                        throw new Error('Не удалось создать серию')
                    }

                    setCreatedActivityId(result.first_activity_id)
                    // Use direct webapp URL for sharing - works in Telegram Mini App
                    setShareLink(`${window.location.origin}/activity/${result.first_activity_id}`)
                    setFlowStep('success') // Skip GPX for recurring
                } else {
                    // Create single activity
                    const result = await createActivity({
                        title,
                        date: formatDateTimeForAPI(date, time),
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
                    // Use direct webapp URL for sharing - works in Telegram Mini App
                    setShareLink(`${window.location.origin}/activity/${result.id}`)
                    // Skip GPX step for yoga and workout
                    if (['yoga', 'workout'].includes(sportType)) {
                        setFlowStep('success')
                    } else {
                        setFlowStep('gpx')
                    }
                }
            }
        } catch (e) {
            showToast(e.message || 'Не удалось сохранить', 'error')
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
        showToast('Ссылка скопирована')
    }

    // Share via Telegram
    const handleShare = () => {
        if (tg.webApp?.openTelegramLink) {
            const text = encodeURIComponent(`Присоединяйся к активности "${title}"!`)
            tg.webApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${text}`)
        } else {
            navigator.clipboard.writeText(shareLink)
            showToast('Ссылка скопирована')
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
                    name="title"
                    label="Название"
                    value={title}
                    onChange={setTitle}
                    placeholder="Утренняя пробежка"
                    error={errors.title}
                    required
                />

                {/* Date & Time */}
                <div className="flex gap-3 mb-2">
                    <div className="flex-1" data-field="date">
                        <label className="text-sm text-gray-700 mb-2 block">
                            Когда <span className="text-red-400">*</span>
                        </label>
                        <div className="relative">
                            <input
                                type="date"
                                value={date}
                                min={new Date().toISOString().split('T')[0]}
                                onChange={(e) => setDate(e.target.value)}
                                disabled={recurringScope === 'this_and_following'}
                                className={`w-full px-4 py-3 border rounded-xl text-sm outline-none transition-colors ${
                                    date ? 'text-gray-800' : 'text-transparent'
                                } ${
                                    errors.date ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
                                } ${
                                    recurringScope === 'this_and_following' ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
                                }`}
                            />
                            {!date && (
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sm text-gray-400 pointer-events-none">
                                    Выберите дату
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="w-28">
                        <label className="text-sm text-gray-700 mb-2 block">&nbsp;</label>
                        <input
                            type="time"
                            value={time}
                            onChange={(e) => setTime(e.target.value)}
                            disabled={recurringScope === 'this_and_following'}
                            className={`w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400 transition-colors ${
                                recurringScope === 'this_and_following' ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : ''
                            }`}
                        />
                    </div>
                </div>
                {/* For recurring 'this_and_following' - date/time is disabled (can't shift entire series) */}
                {recurringScope === 'this_and_following' && (
                    <div className="mb-4 p-3 bg-gray-50 rounded-xl">
                        <p className="text-sm text-gray-500">
                            📅 Дата и время не меняются при редактировании серии.
                            Выберите "Только эту" чтобы перенести одну тренировку.
                        </p>
                    </div>
                )}

                {/* Recurrence Section - only in create mode, after date/time */}
                {!isEditMode && (
                    <div className="mb-4">
                        <label className="text-sm text-gray-700 mb-2 block">Повторение</label>

                        {!canCreateRecurring ? (
                            // Disabled state for non-organizers or public activities
                            <div className="px-4 py-3 bg-gray-50 rounded-xl border border-gray-100">
                                <div className="flex items-center gap-2 text-gray-400">
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                    <span className="text-sm">Только для клубов и групп</span>
                                </div>
                                <p className="text-xs text-gray-400 mt-1">
                                    Создавать повторяющиеся тренировки могут только организаторы
                                </p>
                            </div>
                        ) : (
                            // Enabled state for organizers
                            <div className="space-y-4">
                                <ToggleButtons
                                    options={[
                                        { id: 'single', label: 'Одна тренировка' },
                                        { id: 'recurring', label: 'Повторяющаяся' }
                                    ]}
                                    selected={isRecurring ? 'recurring' : 'single'}
                                    onChange={(val) => setIsRecurring(val === 'recurring')}
                                />

                                {isRecurring && (
                                    <div className="space-y-4 p-4 bg-gray-50 rounded-xl">
                                        {/* Frequency picker */}
                                        <div>
                                            <label className="text-sm text-gray-600 mb-2 block">
                                                Частота
                                            </label>
                                            <DropdownPicker
                                                value={recurrenceFrequency}
                                                options={frequencyOptions}
                                                onChange={setRecurrenceFrequency}
                                            />
                                        </div>

                                        {/* Occurrences count - max 12 (3 months) */}
                                        <div>
                                            <label className="text-sm text-gray-600 mb-2 block">
                                                Количество повторений
                                            </label>
                                            <div className="flex items-center gap-3">
                                                <input
                                                    type="number"
                                                    min={1}
                                                    max={12}
                                                    value={recurrenceCount}
                                                    onChange={(e) => setRecurrenceCount(
                                                        Math.min(12, Math.max(1, parseInt(e.target.value) || 1))
                                                    )}
                                                    className="w-20 px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400"
                                                />
                                                <span className="text-sm text-gray-500">
                                                    (макс. 12 = 3 мес)
                                                </span>
                                            </div>
                                        </div>

                                        {/* Hint about day of week */}
                                        <p className="text-xs text-gray-400">
                                            * Тренировка будет повторяться каждую {date ? dayNamesLong[getDayOfWeekFromDate(date)] : 'неделю в выбранный день'}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                <FormInput
                    name="location"
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
