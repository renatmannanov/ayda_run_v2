import { useState, useEffect, useCallback } from 'react'
import { activitiesApi, clubsApi, groupsApi, tg } from '../api'

/**
 * Generic hook for API calls with loading and error states
 */
export function useApi(apiCall, deps = []) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)
            const result = await apiCall()
            setData(result)
        } catch (err) {
            setError(err.message || 'Ошибка загрузки')
            console.error('API Error:', err)
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
    return useApi(() => clubsApi.get(id), [id])
}

export function useClubMembers(id) {
    return useApi(() => clubsApi.getMembers(id), [id])
}

/**
 * Groups hooks
 */
export function useGroups(clubId = null) {
    return useApi(() => groupsApi.list(clubId), [clubId])
}

export function useGroup(id) {
    return useApi(() => groupsApi.get(id), [id])
}

export function useGroupMembers(id) {
    return useApi(() => groupsApi.getMembers(id), [id])
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
            tg.haptic('error')
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

/**
 * Group actions
 */
export function useJoinGroup() {
    return useMutation((id) => groupsApi.join(id))
}

export function useCreateGroup() {
    return useMutation((data) => groupsApi.create(data))
}
