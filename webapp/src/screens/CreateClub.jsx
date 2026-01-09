import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { FormInput, FormTextarea, SportChips, Button, LoadingScreen, ErrorScreen } from '../components'
import { DropdownPicker, ToggleButtons, FixedAccess, SuccessPopup } from '../components/ui'
import { useCreateClub, useUpdateClub, useClub } from '../hooks'
import { tg } from '../api'
import { useToast } from '../contexts/ToastContext'

export default function CreateClub() {
    const { id } = useParams()
    const isEditMode = !!id
    const navigate = useNavigate()
    const { showToast } = useToast()
    const scrollRef = useRef(null)

    const { mutateAsync: createClub, isPending: creating } = useCreateClub()
    const { mutateAsync: updateClub, isPending: updating } = useUpdateClub()

    // Fetch club if in edit mode
    const { data: existingClub, isLoading: loadingClub, error: errorClub } = useClub(isEditMode ? id : null)

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

    // Visibility options for club
    const visibilityOptions = [
        { id: 'public', icon: '🌐', label: 'Публичный', sublabel: 'все могут найти' },
        { id: 'private', icon: '🔒', label: 'Закрытый', sublabel: 'только по приглашению' }
    ]

    // Access options
    const accessOptions = [
        { id: 'open', label: 'Все желающие' },
        { id: 'request', icon: '🔒', label: 'По заявке' }
    ]

    // Handle visibility change with auto-access fix
    const handleVisibilityChange = (newVisibility) => {
        setVisibility(newVisibility)
        // Private club = access is always 'request'
        if (newVisibility === 'private') {
            setAccess('request')
        }
    }

    const getAccessHint = () => {
        if (visibility === 'private') {
            return 'Закрытый клуб — вступление только по заявке'
        }
        if (access === 'open') {
            return 'Любой может вступить в клуб'
        }
        return 'Нужно одобрение администратора'
    }

    // Populate form when data loads
    useEffect(() => {
        if (existingClub) {
            setName(existingClub.name)
            setDescription(existingClub.description || '')
            setTelegramChat(existingClub.telegramChatId ? existingClub.telegramChatId.toString() : '')

            // Set visibility based on is_private
            if (existingClub.isPrivate) {
                setVisibility('private')
                setAccess('request')
            } else {
                setVisibility('public')
                setAccess(existingClub.isOpen !== false ? 'open' : 'request')
            }
        }
    }, [existingClub])

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
            const payload = {
                name,
                description,
                is_private: visibility === 'private',
                is_open: access === 'open'
            }

            if (isEditMode) {
                await updateClub({ id, data: payload })
                showToast('Изменения сохранены')
                navigate(-1)
            } else {
                const result = await createClub(payload)
                setShareLink(`https://t.me/aydarun_bot?start=club_${result.id}`)
                setCreatedId(result.id)
                setShowSuccess(true)
            }
        } catch (e) {
            showToast(isEditMode ? 'Ошибка при сохранении' : 'Ошибка при создании клуба', 'error')
        }
    }

    // Copy link
    const handleCopyLink = () => {
        navigator.clipboard.writeText(shareLink)
        showToast('Ссылка скопирована')
    }

    // Share (can use Telegram share if available)
    const handleShare = () => {
        if (tg.webApp?.openTelegramLink) {
            const text = encodeURIComponent(`Присоединяйся к клубу "${name}"!`)
            tg.webApp.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareLink)}&text=${text}`)
        } else {
            navigator.clipboard.writeText(shareLink)
            showToast('Ссылка скопирована')
        }
    }

    const handleSuccessDone = () => {
        navigate(`/club/${createdId}`)
    }

    if (isEditMode && loadingClub) return <LoadingScreen />
    if (isEditMode && errorClub) return <ErrorScreen message={errorClub} />

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
                    {isEditMode ? 'Редактировать клуб' : 'Новый клуб'}
                </span>
                <div className="w-16" />
            </div>

            {/* Form */}
            <div ref={scrollRef} className="flex-1 overflow-auto px-4 py-4">
                <FormInput
                    label="Название клуба"
                    value={name}
                    onChange={setName}
                    placeholder="Trail Runners Almaty"
                    error={errors.name}
                    required
                />

                <FormTextarea
                    label="Описание"
                    value={description}
                    onChange={setDescription}
                    placeholder="Бегаем по горам вокруг Алматы. Все уровни подготовки приветствуются!"
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
                    label="Telegram чат клуба"
                    value={telegramChat}
                    onChange={setTelegramChat}
                    placeholder="@trailrunners_almaty"
                    helper={isEditMode && existingClub?.telegramChatId ? "Нельзя изменить после привязки" : "Бот будет отправлять уведомления о тренировках"}
                    disabled={isEditMode && !!existingClub?.telegramChatId}
                />

                <div className="border-t border-gray-200 my-4" />

                {/* Visibility */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
                    <DropdownPicker
                        value={visibility}
                        options={visibilityOptions}
                        onChange={handleVisibilityChange}
                        placeholder="Выбрать..."
                    />
                </div>

                {/* Access */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Кто может вступить?</label>
                    {visibility === 'private' ? (
                        <FixedAccess
                            icon="🔒"
                            label="По заявке"
                            hint={getAccessHint()}
                        />
                    ) : (
                        <ToggleButtons
                            options={accessOptions}
                            selected={access}
                            onChange={setAccess}
                            hint={getAccessHint()}
                        />
                    )}
                </div>
            </div>

            {/* Submit button */}
            <div className="px-4 pb-6 pt-2 border-t border-gray-200">
                <Button
                    onClick={handleSubmit}
                    loading={creating || updating}
                >
                    {isEditMode ? 'Сохранить изменения' : 'Создать клуб'}
                </Button>
            </div>

            {/* Success Popup */}
            <SuccessPopup
                isOpen={showSuccess}
                title="Клуб создан!"
                description="Пригласи участников по ссылке"
                shareLink={shareLink}
                onCopyLink={handleCopyLink}
                onShare={handleShare}
                onDone={handleSuccessDone}
                doneButtonText="Перейти в клуб →"
            />
        </div>
    )
}
