import { useCallback, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { analyticsApi } from '../api'

// Generate unique session ID (persists for tab lifetime)
const getSessionId = () => {
    if (!window.__analyticsSessionId) {
        window.__analyticsSessionId = crypto.randomUUID?.() ||
            `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    }
    return window.__analyticsSessionId
}

/**
 * Analytics hook for tracking user events.
 *
 * Usage:
 * const { trackEvent, trackScreenView } = useAnalytics()
 *
 * trackEvent('activity_join', { activity_id: '123' })
 * trackScreenView('home')
 */
export function useAnalytics() {
    const sessionId = getSessionId()

    const trackEvent = useCallback((eventName, eventParams = null) => {
        // Fire and forget - don't await, don't block UI
        analyticsApi.trackEvent(eventName, eventParams, sessionId).catch((err) => {
            // Silently fail - analytics should never break the app
            console.debug('[Analytics] Failed to track event:', eventName, err.message)
        })
    }, [sessionId])

    const trackScreenView = useCallback((screenName) => {
        trackEvent('screen_view', { screen_name: screenName })
    }, [trackEvent])

    return { trackEvent, trackScreenView, sessionId }
}

/**
 * Hook that automatically tracks screen views on route changes.
 * Use this in App.jsx or main router component.
 */
export function useScreenTracking() {
    const location = useLocation()
    const { trackScreenView } = useAnalytics()
    const prevPathRef = useRef(null)

    useEffect(() => {
        // Skip if same path (prevents double tracking)
        if (prevPathRef.current === location.pathname) return
        prevPathRef.current = location.pathname

        // Map route to screen name
        const screenName = getScreenName(location.pathname)
        trackScreenView(screenName)
    }, [location.pathname, trackScreenView])
}

/**
 * Map route pathname to readable screen name
 */
function getScreenName(pathname) {
    // Exact matches
    const exactRoutes = {
        '/': 'home',
        '/clubs': 'clubs',
        '/profile': 'profile',
        '/statistics': 'statistics',
        '/settings': 'settings',
        '/activity/create': 'activity_create',
        '/club/create': 'club_create',
        '/group/create': 'group_create',
    }

    if (exactRoutes[pathname]) {
        return exactRoutes[pathname]
    }

    // Pattern matches
    if (pathname.match(/^\/activity\/[^/]+\/edit$/)) {
        return 'activity_edit'
    }
    if (pathname.match(/^\/activity\/[^/]+$/)) {
        return 'activity_detail'
    }
    if (pathname.match(/^\/club\/[^/]+$/)) {
        return 'club_detail'
    }
    if (pathname.match(/^\/group\/[^/]+$/)) {
        return 'group_detail'
    }

    // Fallback
    return pathname.replace(/\//g, '_').replace(/^_/, '') || 'unknown'
}

export default useAnalytics
