import { useState, useEffect, useCallback } from 'react'
import { activitiesApi, clubsApi, groupsApi, tg } from '../api'

/**
 * Generic hook for API calls with loading and error states
 */
export function useApi(apiCall, deps = []) {
    const [data, setData] = useState() // undefined to allow default values in destructuring
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)
            console.log('[API] Fetching...', { deps })
            const result = await apiCall()
            console.log('[API] Success:', result)
            setData(result)
        } catch (err) {
            console.error('[API] Error:', err)
            setError(err.message || 'Ошибка загрузки')
            // Don't reset data on error, keep previous or undefined
        } finally {
            setLoading(false)
        }
    }, deps)

    useEffect(() => {
        fetchData()
    }, [fetchData])

    return { data, loading, error, refetch: fetchData, setData }
}

/**
 * Activities hooks
 */
export function useActivities(filters = {}) {
    return useApi(() => activitiesApi.list(filters), [JSON.stringify(filters)])
}

export function useActivity(id) {
    return useApi(() => activitiesApi.get(id), [id])
}

export function useActivityParticipants(id) {
    return useApi(() => activitiesApi.getParticipants(id), [id])
}

/**
 * Clubs hooks
 */
export function useClubs() {
    return useApi(() => clubsApi.list(), [])
}

export function useClub(id) {
    return useApi(() => id ? clubsApi.get(id) : Promise.resolve(null), [id])
}

export function useClubMembers(id) {
    return useApi(() => id ? clubsApi.getMembers(id) : Promise.resolve(null), [id])
}

/**
 * Groups hooks
 */
export function useGroups(clubId = null) {
    return useApi(() => groupsApi.list(clubId), [clubId])
}

export function useGroup(id) {
    return useApi(() => id ? groupsApi.get(id) : Promise.resolve(null), [id])
}

export function useGroupMembers(id) {
    return useApi(() => id ? groupsApi.getMembers(id) : Promise.resolve(null), [id])
}

/**
 * Mutation hooks (for create/update/delete)
 */
export function useMutation(mutationFn) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const mutate = async (...args) => {
        try {
            setLoading(true)
            setError(null)
            const result = await mutationFn(...args)
            tg.haptic('light')
            return result
        } catch (err) {
            setError(err.message || 'Ошибка')
            tg.hapticNotification('error')
            throw err
        } finally {
            setLoading(false)
        }
    }

    return { mutate, loading, error }
}

/**
 * Activity actions
 */
export function useJoinActivity() {
    return useMutation((id) => activitiesApi.join(id))
}

export function useLeaveActivity() {
    return useMutation((id) => activitiesApi.leave(id))
}

export function useCreateActivity() {
    return useMutation((data) => activitiesApi.create(data))
}

/**
 * Club actions
 */
export function useJoinClub() {
    return useMutation((id) => clubsApi.join(id))
}

export function useCreateClub() {
    return useMutation((data) => clubsApi.create(data))
}

export function useUpdateClub() {
    return useMutation((id, data) => clubsApi.update(id, data))
}

export function useDeleteClub() {
    return useMutation((id) => clubsApi.delete(id))
}

/**
 * Group actions
 */
export function useJoinGroup() {
    return useMutation((id) => groupsApi.join(id))
}

export function useCreateGroup() {
    return useMutation((data) => groupsApi.create(data))
}

export function useUpdateGroup() {
    return useMutation((id, data) => groupsApi.update(id, data))
}

export function useDeleteGroup() {
    return useMutation((id) => groupsApi.delete(id))
}
