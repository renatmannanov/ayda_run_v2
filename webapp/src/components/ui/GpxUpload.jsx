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
        <div className="mb-4">
            <label className="text-sm text-gray-700 mb-2 block font-medium">
                GPX Route
            </label>

            <input
                ref={inputRef}
                type="file"
                accept=".gpx"
                onChange={handleFileSelect}
                className="hidden"
            />

            {hasGpx ? (
                // File exists - show info and delete button
                <div className="flex items-center gap-2 px-4 py-3 bg-green-50 border border-green-200 rounded-xl">
                    <span className="text-green-600 text-lg">📍</span>
                    <span className="text-sm text-green-700 flex-1 truncate">
                        {gpxFilename || 'route.gpx'}
                    </span>
                    <button
                        onClick={handleDelete}
                        className="text-red-500 hover:text-red-700 text-sm px-2"
                        title="Delete GPX file"
                    >
                        Delete
                    </button>
                </div>
            ) : (
                // No file - show upload button
                <button
                    onClick={() => inputRef.current?.click()}
                    disabled={uploading}
                    className="px-4 py-3 border border-dashed border-gray-300 rounded-xl text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-colors w-full text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {uploading ? (
                        <span className="flex items-center gap-2">
                            <span className="animate-spin">⏳</span>
                            Uploading...
                        </span>
                    ) : (
                        <span className="flex items-center gap-2">
                            <span>📍</span>
                            Add GPX file
                        </span>
                    )}
                </button>
            )}

            {error && (
                <p className="text-red-500 text-sm mt-2">{error}</p>
            )}
        </div>
    )
}

export default GpxUpload
