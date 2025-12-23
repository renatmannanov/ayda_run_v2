import { useState, useRef } from 'react'
import { activitiesApi } from '../../api'

/**
 * GPX file upload component
 *
 * Shows upload button for activities without GPX,
 * or file info with delete button for activities with GPX.
 */
export function GpxUpload({ activityId, hasGpx, gpxFilename, onSuccess, onError }) {
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState(null)
    const inputRef = useRef()

    const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

    const handleFileSelect = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        // Reset error
        setError(null)

        // Validate extension
        if (!file.name.toLowerCase().endsWith('.gpx')) {
            setError('Only .gpx files are allowed')
            return
        }

        // Validate size
        if (file.size > MAX_FILE_SIZE) {
            setError('File too large. Maximum size is 20MB')
            return
        }

        setUploading(true)

        try {
            await activitiesApi.uploadGpx(activityId, file)
            onSuccess?.()
        } catch (err) {
            const errorMessage = err.message || 'Failed to upload GPX file'
            setError(errorMessage)
            onError?.(errorMessage)
        } finally {
            setUploading(false)
            // Reset input so same file can be selected again
            if (inputRef.current) {
                inputRef.current.value = ''
            }
        }
    }

    const handleDelete = async () => {
        if (!window.confirm('Delete GPX file?')) return

        try {
            await activitiesApi.deleteGpx(activityId)
            onSuccess?.()
        } catch (err) {
            const errorMessage = err.message || 'Failed to delete GPX file'
            setError(errorMessage)
            onError?.(errorMessage)
        }
    }

    return (
        <>
            <input
                ref={inputRef}
                type="file"
                accept=".gpx"
                onChange={handleFileSelect}
                className="hidden"
            />

            <button
                onClick={() => inputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 transition-colors py-1 disabled:opacity-50"
            >
                <span className="w-5 text-center">⚡</span>
                <span className="font-medium">
                    {uploading ? 'Загрузка...' : 'Добавить GPX файл'}
                </span>
            </button>

            {error && (
                <p className="text-red-500 text-xs mt-1">{error}</p>
            )}
        </>
    )
}

export default GpxUpload
