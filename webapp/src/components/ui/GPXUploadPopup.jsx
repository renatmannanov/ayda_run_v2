import React, { useState, useRef, useEffect } from 'react'
import { activitiesApi } from '../../api'

/**
 * GPX Upload Popup
 *
 * Modes:
 * - 'create': After activity creation, optional upload with Skip button
 * - 'add': Adding GPX to existing activity
 * - 'edit': Replacing existing GPX file
 */
export default function GPXUploadPopup({
    isOpen,
    onClose,
    onSkip,
    onUpload,
    mode = 'create',
    existingFile = null,
    activityId = null
}) {
    const [file, setFile] = useState(existingFile)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const inputRef = useRef()

    const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

    // Reset file when popup opens/closes or existingFile changes
    useEffect(() => {
        if (isOpen) {
            setFile(existingFile)
            setError(null)
        }
    }, [isOpen, existingFile])

    if (!isOpen) return null

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files?.[0]
        if (!selectedFile) return

        setError(null)

        // Validate extension
        if (!selectedFile.name.toLowerCase().endsWith('.gpx')) {
            setError('Только .gpx файлы')
            return
        }

        // Validate size
        if (selectedFile.size > MAX_FILE_SIZE) {
            setError('Файл слишком большой. Максимум 20MB')
            return
        }

        setFile({
            name: selectedFile.name,
            size: (selectedFile.size / 1024).toFixed(1) + ' KB',
            rawFile: selectedFile
        })

        // Reset input for re-selection
        if (inputRef.current) {
            inputRef.current.value = ''
        }
    }

    const handleRemoveFile = () => {
        setFile(null)
        setError(null)
    }

    const getTitle = () => {
        switch (mode) {
            case 'edit': return 'Изменить GPX'
            case 'add': return 'Добавить GPX'
            default: return 'Добавить маршрут'
        }
    }

    const getDescription = () => {
        switch (mode) {
            case 'edit': return 'Загрузите новый GPX файл для замены текущего маршрута'
            case 'add': return 'Загрузите GPX файл с маршрутом тренировки'
            default: return 'Хотите добавить GPX файл с маршрутом? Это поможет участникам лучше подготовиться.'
        }
    }

    const getSubmitText = () => {
        if (uploading) return 'Загрузка...'
        if (!file) return mode === 'create' ? 'Готово' : 'Отмена'
        switch (mode) {
            case 'edit': return 'Сохранить'
            case 'add': return 'Добавить'
            default: return 'Готово'
        }
    }

    const handleSubmit = async () => {
        if (file?.rawFile && activityId) {
            // Upload new file
            setUploading(true)
            setError(null)
            try {
                await activitiesApi.uploadGpx(activityId, file.rawFile)
                onUpload?.(file)
            } catch (err) {
                setError(err.message || 'Ошибка загрузки')
                setUploading(false)
                return
            }
            setUploading(false)
        } else if (file && !file.rawFile && mode === 'edit') {
            // No new file selected in edit mode, just close
            onClose()
        } else if (!file) {
            // No file selected
            if (mode === 'create') {
                onSkip?.()
            } else {
                onClose()
            }
        } else {
            // File selected but no activityId (shouldn't happen normally)
            onUpload?.(file)
        }
    }

    const handleDelete = async () => {
        if (!activityId) return

        setUploading(true)
        setError(null)
        try {
            await activitiesApi.deleteGpx(activityId)
            setFile(null)
            onUpload?.(null)
        } catch (err) {
            setError(err.message || 'Ошибка удаления')
        }
        setUploading(false)
    }

    return (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/30"
                onClick={onClose}
            />

            {/* Bottom Sheet */}
            <div className="relative bg-white rounded-t-2xl w-full max-w-md overflow-hidden">
                {/* Header */}
                <div className="px-4 pt-4 pb-2">
                    <div className="flex items-center justify-between">
                        <h3 className="text-base font-medium text-gray-800">{getTitle()}</h3>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 p-1"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{getDescription()}</p>
                </div>

                {/* Content */}
                <div className="px-4 py-4">
                    <input
                        ref={inputRef}
                        type="file"
                        accept=".gpx"
                        onChange={handleFileSelect}
                        className="hidden"
                        disabled={uploading}
                    />

                    {uploading ? (
                        /* Loading state */
                        <div className="border border-gray-200 rounded-xl p-6 text-center">
                            <div className="w-8 h-8 border-2 border-gray-200 border-t-gray-800 rounded-full animate-spin mx-auto mb-3" />
                            <p className="text-sm text-gray-600 font-medium">Проверяем и загружаем файл</p>
                            <p className="text-xs text-gray-400 mt-1">Это может занять несколько секунд</p>
                        </div>
                    ) : !file ? (
                        /* Upload button */
                        <label
                            onClick={() => inputRef.current?.click()}
                            className="block border border-gray-200 rounded-xl p-4 text-center cursor-pointer hover:bg-gray-50 transition-colors"
                        >
                            <div className="text-2xl mb-2">📍</div>
                            <p className="text-sm text-gray-600 font-medium">Выбрать GPX файл</p>
                        </label>
                    ) : (
                        /* File preview */
                        <div className="border border-gray-200 rounded-xl p-4">
                            <div className="flex items-start gap-3">
                                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                    <span className="text-lg">📍</span>
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
                                    {file.size && <p className="text-xs text-gray-400 mt-0.5">{file.size}</p>}
                                </div>
                                <button
                                    onClick={mode === 'edit' && !file.rawFile ? handleDelete : handleRemoveFile}
                                    disabled={uploading}
                                    className="text-gray-400 hover:text-gray-600 p-1 disabled:opacity-50"
                                >
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                            {/* Option to replace file */}
                            {mode === 'edit' && (
                                <button
                                    onClick={() => inputRef.current?.click()}
                                    className="mt-3 text-xs text-gray-500 hover:text-gray-700 underline"
                                >
                                    Выбрать другой файл
                                </button>
                            )}
                        </div>
                    )}

                    {error && (
                        <p className="text-red-500 text-xs mt-2">{error}</p>
                    )}
                </div>

                {/* Actions */}
                <div className="px-4 pb-8 flex gap-3">
                    {mode === 'create' && !file && (
                        <button
                            onClick={onSkip}
                            disabled={uploading}
                            className="flex-1 py-3 text-sm text-gray-500 hover:text-gray-700 transition-colors disabled:opacity-50"
                        >
                            Пропустить
                        </button>
                    )}
                    <button
                        onClick={handleSubmit}
                        disabled={uploading}
                        className={`flex-1 py-3 rounded-xl text-sm font-medium transition-colors disabled:opacity-50 ${
                            file
                                ? 'bg-gray-800 text-white hover:bg-gray-700'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                    >
                        {getSubmitText()}
                    </button>
                </div>
            </div>
        </div>
    )
}
