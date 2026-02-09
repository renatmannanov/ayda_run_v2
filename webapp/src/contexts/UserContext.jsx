import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { usersApi } from '../api'
import { useApi } from '../hooks'

const UserContext = createContext(null)

export function UserProvider({ children }) {
    const { data: userProfile, refetch, isLoading } = useApi(usersApi.getMe)
    const [showPhoto, setShowPhoto] = useState(false)
    const [stravaConnected, setStravaConnected] = useState(false)
    const [updating, setUpdating] = useState(false)

    // Sync state from userProfile
    useEffect(() => {
        if (userProfile) {
            setShowPhoto(userProfile.showPhoto === true)
            setStravaConnected(userProfile.stravaConnected === true)
        }
    }, [userProfile])

    // Update showPhoto setting
    const updateShowPhoto = useCallback(async (value) => {
        setShowPhoto(value)
        setUpdating(true)
        try {
            await usersApi.updateProfile({ showPhoto: value })
            await refetch()
        } catch (err) {
            // Revert on error
            setShowPhoto(!value)
        } finally {
            setUpdating(false)
        }
    }, [refetch])

    // Connect Strava via OAuth popup
    const connectStrava = useCallback(async () => {
        setUpdating(true)
        try {
            const { url } = await usersApi.stravaAuthUrl()
            const popup = window.open(url, '_blank', 'width=600,height=700')

            return new Promise((resolve) => {
                // Listen for postMessage from OAuth callback page
                const handler = async (event) => {
                    if (event.data === 'strava-connected') {
                        window.removeEventListener('message', handler)
                        clearInterval(interval)
                        await refetch()
                        setUpdating(false)
                        resolve(true)
                    }
                }
                window.addEventListener('message', handler)

                // Fallback: poll for popup close, then refetch
                const interval = setInterval(async () => {
                    if (popup && popup.closed) {
                        clearInterval(interval)
                        window.removeEventListener('message', handler)
                        await refetch()
                        setUpdating(false)
                        resolve(false)
                    }
                }, 1000)
            })
        } catch (err) {
            setUpdating(false)
            return false
        }
    }, [refetch])

    // Disconnect Strava
    const disconnectStrava = useCallback(async () => {
        setStravaConnected(false) // Optimistic update
        setUpdating(true)
        try {
            await usersApi.stravaDisconnect()
            await refetch()
        } catch (err) {
            setStravaConnected(true) // Revert on error
        } finally {
            setUpdating(false)
        }
    }, [refetch])

    const value = {
        user: userProfile,
        isLoading,
        showPhoto,
        stravaConnected,
        updating,
        updateShowPhoto,
        connectStrava,
        disconnectStrava,
        refetch,
    }

    return (
        <UserContext.Provider value={value}>
            {children}
        </UserContext.Provider>
    )
}

export function useUser() {
    const context = useContext(UserContext)
    // Return null-safe default if used outside provider
    if (!context) {
        return {
            user: null,
            isLoading: false,
            showPhoto: false,
            stravaConnected: false,
            updating: false,
            updateShowPhoto: () => {},
            connectStrava: () => Promise.resolve(false),
            disconnectStrava: () => Promise.resolve(false),
            refetch: () => {},
        }
    }
    return context
}

export default UserContext
