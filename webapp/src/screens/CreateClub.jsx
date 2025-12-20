import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { FormInput, FormTextarea, FormRadioGroup, SportChips, Button, LoadingScreen, ErrorScreen } from '../components'
import { useCreateClub, useUpdateClub, useClub } from '../hooks'

export default function CreateClub() {
    const { id } = useParams()
    const isEditMode = !!id
    const navigate = useNavigate()

    const { mutate: createClub, loading: creating } = useCreateClub()
    const { mutate: updateClub, loading: updating } = useUpdateClub()

    // Fetch club if in edit mode
    // We pass id only if editing, else null to skip fetch
    const { data: existingClub, loading: loadingClub, error: errorClub } = useClub(isEditMode ? id : null)

    // Form state
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [selectedSports, setSelectedSports] = useState([])
    const [telegramChat, setTelegramChat] = useState('')
    const [visibility, setVisibility] = useState('public')
    const [errors, setErrors] = useState({})
    const [isCreated, setIsCreated] = useState(false)
    const [shareLink, setShareLink] = useState('')
    const [createdId, setCreatedId] = useState(null)

    // Populate form when data loads
    useEffect(() => {
        if (existingClub) {
            setName(existingClub.name)
            setDescription(existingClub.description || '')
            // setSelectedSports(existingClub.sport_types || [])
            setTelegramChat(existingClub.telegramChatId ? existingClub.telegramChatId.toString() : '') // TODO: handle telegram integration
            // setVisibility(existingClub.is_private ? 'private' : 'public')
        }
    }, [existingClub])

    const visibilityOptions = [
        { id: 'public', label: 'Публичный', description: 'Все могут найти и вступить' },
        { id: 'private', label: 'По ссылке', description: 'Только по приглашению' }
    ]

    // Validation
    const validate = () => {
        const newErrors = {}
        if (!name.trim()) newErrors.name = true
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    // Submit
    const handleSubmit = async () => {
        if (validate()) {
            try {
                const payload = {
                    name,
                    description,
                    is_open: visibility !== 'private', // public = open, private = closed
                    // sport_types: selectedSports, // Not supported by backend yet
                    // telegram_chat_id: telegramChat, // Backend needs INT, not string username
                }

                if (isEditMode) {
                    await updateClub(id, payload)
                    navigate(-1) // Go back to detail
                } else {
                    const result = await createClub(payload)
                    // Assuming result contains share link or invite code
                    setShareLink('https://t.me/aydarun_bot?start=club_' + result.id)
                    setCreatedId(result.id)
                    setIsCreated(true)
                }
            } catch (e) {
                console.error('Failed to save club', e)
                alert(isEditMode ? 'Ошибка при сохранении' : 'Ошибка при создании клуба')
            }
        }
    }

    // Copy link
    const copyLink = () => {
        navigator.clipboard.writeText(shareLink)
        alert('Ссылка скопирована!')
    }

    if (isEditMode && loadingClub) return <LoadingScreen />
    if (isEditMode && errorClub) return <ErrorScreen message={errorClub} />

    // Success screen (Create Only)
    if (isCreated) {
        return (
            <div className="min-h-screen bg-white flex flex-col">
                <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
                    <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-6">
                        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>

                    <h1 className="text-xl text-gray-800 font-medium mb-2">
                        Клуб создан!
                    </h1>
                    <p className="text-sm text-gray-500 mb-8">
                        Пригласи участников по ссылке
                    </p>

                    <div className="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
                        <p className="text-xs text-gray-400 mb-2">Ссылка для приглашения</p>
                        <p className="text-sm text-gray-800 break-all">{shareLink}</p>
                    </div>

                    <div className="flex gap-3 w-full">
                        <Button
                            onClick={copyLink}
                            variant="outline"
                            className="flex-1"
                        >
                            Копировать
                        </Button>
                        <Button className="flex-1">
                            Поделиться
                        </Button>
                    </div>
                </div>

                <div className="px-4 pb-6">
                    <button
                        onClick={() => navigate(`/club/${createdId}`)}
                        className="w-full py-4 text-gray-500 text-sm hover:text-gray-700 transition-colors"
                    >
                        Перейти в клуб →
                    </button>
                </div>
            </div>
        )
    }

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
            <div className="flex-1 overflow-auto px-4 py-4">
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
                    helper="Бот будет отправлять уведомления о тренировках"
                />

                <div className="border-t border-gray-200 my-4" />

                <FormRadioGroup
                    label="Видимость"
                    options={visibilityOptions}
                    value={visibility}
                    onChange={setVisibility}
                />
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
        </div>
    )
}
