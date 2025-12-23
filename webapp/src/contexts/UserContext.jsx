import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { usersApi } from '../api'
import { useApi } from '../hooks'

const UserContext = createContext(null)

export function UserProvider({ children }) {
    const { data: userProfile, refetch, isLoading } = useApi(usersApi.getMe)
    const [showPhoto, setShowPhoto] = useState(false)
    const [updating, setUpdating] = useState(false)

    // Sync showPhoto from userProfile
    useEffect(() => {
        if (userProfile) {
            setShowPhoto(userProfile.showPhoto === true)
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
            console.error('Failed to update showPhoto:', err)
            // Revert on error
            setShowPhoto(!value)
        } finally {
            setUpdating(false)
        }
    }, [refetch])

    // Update strava link
    const updateStravaLink = useCallback(async (stravaLink) => {
        setUpdating(true)
        try {
            await usersApi.updateProfile({ stravaLink })
            await refetch()
            return true
        } catch (err) {
            console.error('Failed to update stravaLink:', err)
            return false
        } finally {
            setUpdating(false)
        }
    }, [refetch])

    // Remove strava link
    const removeStravaLink = useCallback(async () => {
        setUpdating(true)
        try {
            await usersApi.updateProfile({ stravaLink: '' })
            await refetch()
            return true
        } catch (err) {
            console.error('Failed to remove stravaLink:', err)
            return false
        } finally {
            setUpdating(false)
        }
    }, [refetch])

    const value = {
        user: userProfile,
        isLoading,
        showPhoto,
        updating,
        updateShowPhoto,
        updateStravaLink,
        removeStravaLink,
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
            updating: false,
            updateShowPhoto: () => {},
            updateStravaLink: () => Promise.resolve(false),
            removeStravaLink: () => Promise.resolve(false),
            refetch: () => {},
        }
    }
    return context
}

export default UserContext
