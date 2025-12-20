import React from 'react'

/**
 * Avatar component with fallback to initials
 *
 * @param {Object} props
 * @param {string} props.src - Image URL or Telegram file_id
 * @param {string} props.name - Name for initials fallback
 * @param {string} props.size - Size: 'sm', 'md', 'lg', 'xl' (default: 'md')
 * @param {string} props.className - Additional CSS classes
 */
export default function Avatar({ src, name, size = 'md', className = '' }) {
    const [imageError, setImageError] = React.useState(false)

    // Size mappings
    const sizeClasses = {
        'sm': 'w-8 h-8 text-xs',
        'md': 'w-10 h-10 text-sm',
        'lg': 'w-12 h-12 text-base',
        'xl': 'w-16 h-16 text-lg'
    }

    const sizeClass = sizeClasses[size] || sizeClasses.md

    // Generate initials from name
    const getInitials = (name) => {
        if (!name) return '?'

        const parts = name.trim().split(/\s+/)
        if (parts.length === 1) {
            return parts[0].charAt(0).toUpperCase()
        }

        return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
    }

    // Generate color from name (consistent hash-based color)
    const getColorFromName = (name) => {
        if (!name) return 'bg-gray-400'

        const colors = [
            'bg-blue-500',
            'bg-green-500',
            'bg-yellow-500',
            'bg-red-500',
            'bg-purple-500',
            'bg-pink-500',
            'bg-indigo-500',
            'bg-teal-500'
        ]

        // Simple hash function
        let hash = 0
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash)
        }

        return colors[Math.abs(hash) % colors.length]
    }

    const initials = getInitials(name)
    const bgColor = getColorFromName(name)

    // Convert Telegram file_id to URL if needed
    const getImageUrl = (src) => {
        if (!src) return null

        // If it's a Telegram file_id (doesn't start with http), construct URL
        if (!src.startsWith('http')) {
            // TODO: Implement Telegram file URL construction
            // For now, treat as invalid
            return null
        }

        return src
    }

    const imageUrl = getImageUrl(src)
    const showImage = imageUrl && !imageError

    return (
        <div
            className={`${sizeClass} rounded-full flex items-center justify-center flex-shrink-0 ${className}`}
        >
            {showImage ? (
                <img
                    src={imageUrl}
                    alt={name || 'Avatar'}
                    className="w-full h-full rounded-full object-cover"
                    onError={() => setImageError(true)}
                />
            ) : (
                <div className={`w-full h-full rounded-full ${bgColor} flex items-center justify-center text-white font-medium`}>
                    {initials}
                </div>
            )}
        </div>
    )
}
