import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { FormInput, FormTextarea, FormCheckbox, FormRadioGroup, Button, LoadingScreen, ErrorScreen } from '../components'
import { useClubs, useCreateGroup, useUpdateGroup, useGroup } from '../hooks'

export default function CreateGroup() {
    const { id } = useParams()
    const isEditMode = !!id
    const navigate = useNavigate()

    const { data: clubs = [] } = useClubs()
    const { mutate: createGroup, loading: creating } = useCreateGroup()
    const { mutate: updateGroup, loading: updating } = useUpdateGroup()

    // Fetch group if in edit mode
    const { data: existingGroup, loading: loadingGroup, error: errorGroup } = useGroup(isEditMode ? id : null)

    // Form state
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [selectedClub, setSelectedClub] = useState('')
    const [isIndependent, setIsIndependent] = useState(false)
    const [telegramChat, setTelegramChat] = useState('')
    const [joinAccess, setJoinAccess] = useState('club')
    const [errors, setErrors] = useState({})
    const [showClubPicker, setShowClubPicker] = useState(false)
    const [isCreated, setIsCreated] = useState(false)
    const [shareLink, setShareLink] = useState('')
    const [createdId, setCreatedId] = useState(null)

    // Populate form
    useEffect(() => {
        if (existingGroup) {
            setName(existingGroup.name)
            setDescription(existingGroup.description || '')
            setTelegramChat(existingGroup.telegramChatId ? existingGroup.telegramChatId.toString() : '') // TODO

            if (existingGroup.clubId) {
                setSelectedClub(existingGroup.clubId.toString())
                setIsIndependent(false)
            } else {
                setSelectedClub('')
                setIsIndependent(true)
            }

            // Map backend 'is_open' to UI state
            // If private (is_open=false), joinAccess is 'invite'
            // If public (is_open=true), joinAccess is 'club' or whatever default is suitable for standalone
            setJoinAccess(existingGroup.isOpen ? 'club' : 'invite')
        }
    }, [existingGroup])

    const joinAccessOptions = [
        { id: 'club', label: 'Открытая', description: 'Любой может вступить' }, // Changed label for clarity in standalone context too
        { id: 'invite', label: 'Только по приглашению', description: 'Нужна ссылка для вступления' }
    ]

    // Get selectable clubs (only those user is member of)
    const myClubs = clubs.filter(c => c.isMember)

    // Get selected club name
    const getSelectedClubName = () => {
        if (isIndependent) return '—'
        const club = myClubs.find(c => c.id.toString() === selectedClub)
        return club ? club.name : 'Выбрать клуб...'
    }

    // Toggle independent
    const toggleIndependent = (checked) => {
        setIsIndependent(checked)
        if (checked) {
            setSelectedClub('')
            setJoinAccess('invite')
        }
    }

    // Validation
    const validate = () => {
        const newErrors = {}
        if (!name.trim()) newErrors.name = true
        if (!isIndependent && !selectedClub) newErrors.club = true
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
                    club_id: isIndependent || !selectedClub ? null : selectedClub,
                    // telegram_chat_id: telegramChat, // Backend needs INT
                    is_open: joinAccess !== 'invite' // Public if not invite-only
                }

                if (isEditMode) {
                    await updateGroup({ id, data: payload })
                    navigate(-1)
                } else {
                    const result = await createGroup(payload)
                    setShareLink('https://t.me/aydarun_bot?start=group_' + result.id)
                    setCreatedId(result.id)
                    setIsCreated(true)
                }
            } catch (e) {
                console.error('Failed to save group', e)
                if (e.message && e.message.includes('Insufficient permissions')) {
                    alert(isEditMode ? 'У вас нет прав на редактирование этой группы' : 'Только организатор клуба может создавать группы')
                } else {
                    alert(isEditMode ? 'Ошибка при сохранении' : 'Ошибка при создании группы')
                }
            }
        }
    }

    // Copy link
    const copyLink = () => {
        navigator.clipboard.writeText(shareLink)
        alert('Ссылка скопирована!')
    }

    // Club picker popup
    const ClubPicker = () => (
        <div
            className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
            onClick={() => setShowClubPicker(false)}
        >
            <div
                className="bg-white w-full max-w-md rounded-t-2xl p-6"
                onClick={e => e.stopPropagation()}
            >
                <h3 className="text-base font-medium text-gray-800 mb-4">Выбрать клуб</h3>

                {myClubs.map(club => (
                    <button
                        key={club.id}
                        onClick={() => {
                            setSelectedClub(club.id.toString())
                            setShowClubPicker(false)
                        }}
                        className={`w-full text-left py-3 px-2 rounded-lg flex items-center gap-3 transition-colors ${selectedClub === club.id.toString() ? 'bg-gray-100' : 'hover:bg-gray-50'
                            }`}
                    >
                        <span className="text-xl">🏆</span>
                        <span className="text-sm text-gray-700">{club.name}</span>
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

    if (isEditMode && loadingGroup) return <LoadingScreen />
    if (isEditMode && errorGroup) return <ErrorScreen message={errorGroup} />

    // Success screen
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
                        Группа создана!
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
                        onClick={() => navigate(`/group/${createdId}`)}
                        className="w-full py-4 text-gray-500 text-sm hover:text-gray-700 transition-colors"
                    >
                        Перейти в группу →
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
                    {isEditMode ? 'Редактировать группу' : 'Новая группа'}
                </span>
                <div className="w-16" />
            </div>

            {/* Form */}
            <div className="flex-1 overflow-auto px-4 py-4">
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

                <div className="border-t border-gray-200 my-4" />

                {/* Club selector */}
                <div className="mb-4">
                    <label className="text-sm text-gray-700 mb-2 block">Часть клуба?</label>
                    <button
                        onClick={() => !isIndependent && !isEditMode && setShowClubPicker(true)}
                        disabled={isIndependent || isEditMode}
                        className={`w-full px-4 py-3 border rounded-xl text-sm text-left flex items-center justify-between transition-colors ${isIndependent || isEditMode
                            ? 'border-gray-100 bg-gray-50 text-gray-400'
                            : errors.club
                                ? 'border-red-300 bg-red-50 text-gray-800'
                                : 'border-gray-200 text-gray-800 hover:border-gray-300'
                            }`}
                    >
                        <span className={selectedClub && !isIndependent ? 'text-gray-800' : 'text-gray-400'}>
                            {getSelectedClubName()}
                        </span>
                        {!isIndependent && !isEditMode && <span className="text-gray-400">▾</span>}
                    </button>
                    {isEditMode && (
                        <p className="text-xs text-gray-400 mt-1">Нельзя изменить привязку к клубу</p>
                    )}

                    {!isEditMode && (
                        <div className="mt-3">
                            <FormCheckbox
                                label="Независимая группа"
                                checked={isIndependent}
                                onChange={toggleIndependent}
                            />
                        </div>
                    )}
                </div>

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

                <FormRadioGroup
                    label="Кто может вступить?"
                    options={isIndependent ? [joinAccessOptions[1]] : joinAccessOptions}
                    value={joinAccess}
                    onChange={setJoinAccess}
                />
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

            {/* Club picker */}
            {showClubPicker && <ClubPicker />}
        </div>
    )
}
