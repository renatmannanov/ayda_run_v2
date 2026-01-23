import React from 'react'

/**
 * Converts URLs in text to clickable links
 * Opens links via Telegram WebApp openLink for proper handling
 */
export default function Linkify({ children, className = '' }) {
    if (!children || typeof children !== 'string') {
        return children
    }

    const urlRegex = /(https?:\/\/[^\s]+)/g
    const parts = children.split(urlRegex)

    if (parts.length === 1) {
        return <span className={className}>{children}</span>
    }

    return (
        <span className={className}>
            {parts.map((part, i) => {
                if (part.match(urlRegex)) {
                    // Truncate long URLs for display
                    const displayUrl = part.length > 50
                        ? part.substring(0, 47) + '...'
                        : part
                    return (
                        <a
                            key={i}
                            href={part}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 underline break-all"
                            onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                if (window.Telegram?.WebApp?.openLink) {
                                    window.Telegram.WebApp.openLink(part)
                                } else {
                                    window.open(part, '_blank')
                                }
                            }}
                        >
                            {displayUrl}
                        </a>
                    )
                }
                return part
            })}
        </span>
    )
}
