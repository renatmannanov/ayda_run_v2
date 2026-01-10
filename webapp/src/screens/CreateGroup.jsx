import React, { useState, useEffect, useMemo, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { FormInput, FormTextarea, SportChips, Button, LoadingScreen, ErrorScreen } from '../components'
import { DropdownPicker, ToggleButtons, SuccessPopup } from '../components/ui'
import { useClubs, useCreateGroup, useUpdateGroup, useGroup } from '../hooks'
import { tg, configApi } from '../api'
import { useToast } from '../contexts/ToastContext'

export default function CreateGroup() {
    const { id } = useParams()
    const isEditMode = !!id
    const navigate = useNavigate()
    const { showToast } = useToast()
    const scrollRef = useRef(null)

    const { data: clubs = [] } = useClubs()
    const { mutateAsync: createGroup, isPending: creating } = useCreateGroup()
    const { mutateAsync: updateGroup, isPending: updating } = useUpdateGroup()

    // Fetch group if in edit mode
    const { data: existingGroup, isLoading: loadingGroup, error: errorGroup } = useGroup(isEditMode ? id : null)

    // Scroll to top on mount
    useEffect(() => {
        scrollRef.current?.scrollTo(0, 0)
    }, [])

    // Form state
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [selectedSports, setSelectedSports] = useState([])
    const [telegramChat, setTelegramChat] = useState('')
    const [visibility, setVisibility] = useState('public')
    const [access, setAccess] = useState('open')
    const [errors, setErrors] = useState({})

    // Success state
    const [showSuccess, setShowSuccess] = useState(false)
    const [shareLink, setShareLink] = useState('')
    const [createdId, setCreatedId] = useState(null)

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
                sublabel: 'только участники клуба'
            })
        })

        return options
    }, [clubs])

    // Access options
    const accessOptions = [
        { id: 'open', label: 'Все желающие' },
        { id: 'request', icon: '🔒', label: 'По заявке' }
    ]

    const getAccessHint = () => {
        if (access === 'open') {
            return visibility === 'public'
                ? 'Любой может вступить в группу'
                : 'Любой участник клуба может вступить'
        }
        return 'Нужно одобрение администратора'
    }

    // Parse visibility for API
    const parseVisibility = (vis) => {
        if (vis === 'public') {
            return { club_id: null }
        }
        if (vis.startsWith('club_')) {
            return { club_id: vis.replace('club_', '') }
        }
        return { club_id: null }
    }

    // Populate form
    useEffect(() => {
        if (existingGroup) {
            setName(existingGroup.name)
            setDescription(existingGroup.description || '')
            setTelegramChat(existingGroup.telegramChatId ? existingGroup.telegramChatId.toString() : '')

            // Set visibility
            if (existingGroup.clubId) {
                setVisibility(`club_${existingGroup.clubId}`)
            } else {
                setVisibility('public')
            }

            // Set access
            setAccess(existingGroup.isOpen !== false ? 'open' : 'request')
        }
    }, [existingGroup])

    // Validation
    const validate = () => {
        const newErrors = {}
        if (!name.trim()) newErrors.name = true
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    // Submit
    const handleSubmit = async () => {
        if (!validate()) return

        try {
            const { club_id } = parseVisibility(visibility)

            const payload = {
                name,
                description,
                club_id,
                is_open: access === 'open'
            }

            if (isEditMode) {
                await updateGroup({ id, data: payload })
                showToast('Изменения сохранены')
                navigate(-1)
            } else {
                const result = await createGroup(payload)
                const botUsername = await configApi.getBotUsername()
                setShareLink(`https://t.me/${botUsername}?start=group_${result.id}`)
                setCreatedId(result.id)
                setShowSuccess(true)
            }
        } catch (e) {
            if (e.message && e.message.includes('Insufficient permissions')) {
                showToast(isEditMode ? 'Нет прав на редактирование' : 'Только организатор может создавать группы', 'error')
            } else {
                showToast(isEditMode ? 'Ошибка при сохранении' : 'Ошибка при создании группы', 'error')
            }
        }
    }

    // Copy link
    const handleCopyLink = () => {
        navigator.clipboard.writeText(shareLink)
        showToast('Ссылка скопирована')
    }

    // Share
    const handleShare = () => {
        if (tg.webApp?.openTelegramLink) {
            const text = encodeURIComponent(`Присоединяйся к группе "${name}"!`)
            tg.webApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${text}`)
        } else {
            navigator.clipboard.writeText(shareLink)
            showToast('Ссылка скопирована')
        }
    }

    const handleSuccessDone = () => {
        navigate(`/group/${createdId}`)
    }

    if (isEditMode && loadingGroup) return <LoadingScreen />
    if (isEditMode && errorGroup) return <ErrorScreen message={errorGroup} />

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
                    {isEditMode ? 'Редактировать группу' : 'Новая группа'}
                </span>
                <div className="w-16" />
            </div>

            {/* Form */}
            <div ref={scrollRef} className="flex-1 overflow-auto px-4 py-4">
                <FormInput
                    label="Название группы"
                    value={name}
                    onChange={setName}
                    placeholder="Вечерние интервалы"
                    error={errors.name}
                    required
                />

                <FormTextarea
                    label="Описание"
                    value={description}
                    onChange={setDescription}
                    placeholder="Скоростные тренировки по вторникам и четвергам"
                    rows={4}
                />

                <SportChips
                    selected={selectedSports}
                    onChange={setSelectedSports}
                    multiple={true}
                    label="Виды активностей"
                />

                <div className="border-t border-gray-200 my-4" />

                <FormInput
                    label="Telegram чат группы"
                    value={telegramChat}
                    onChange={setTelegramChat}
                    placeholder="@srg_intervals"
                    helper={isEditMode && existingGroup?.telegramChatId ? "Нельзя изменить после привязки" : "Можно использовать тот же чат, что у клуба"}
                    disabled={isEditMode && !!existingGroup?.telegramChatId}
                />

                <div className="border-t border-gray-200 my-4" />

                {/* Visibility */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
                    <DropdownPicker
                        value={visibility}
                        options={visibilityOptions}
                        onChange={setVisibility}
                        placeholder="Выбрать..."
                        disabled={isEditMode}
                    />
                    {isEditMode && (
                        <p className="text-xs text-gray-400 mt-1">Нельзя изменить привязку к клубу</p>
                    )}
                </div>

                {/* Access */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Кто может вступить?</label>
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
                    loading={creating || updating}
                >
                    {isEditMode ? 'Сохранить изменения' : 'Создать группу'}
                </Button>
            </div>

            {/* Success Popup */}
            <SuccessPopup
                isOpen={showSuccess}
                title="Группа создана!"
                description="Пригласи участников по ссылке"
                shareLink={shareLink}
                onCopyLink={handleCopyLink}
                onShare={handleShare}
                onDone={handleSuccessDone}
                doneButtonText="Перейти в группу →"
            />
        </div>
    )
}
