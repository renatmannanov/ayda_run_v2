import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { activitiesApi, analyticsApi } from '../api'

// Helper to track analytics events (fire and forget)
const trackEvent = (eventName: string, params?: Record<string, any>) => {
  analyticsApi.trackEvent(eventName, params).catch(() => {})
}

// Query keys for activities
export const activitiesKeys = {
  all: ['activities'] as const,
  lists: () => [...activitiesKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...activitiesKeys.lists(), filters] as const,
  details: () => [...activitiesKeys.all, 'detail'] as const,
  detail: (id: number) => [...activitiesKeys.details(), id] as const,
  participants: (id: number) => [...activitiesKeys.detail(id), 'participants'] as const,
}

// List activities with optional filters
export function useActivities(filters = {}) {
  return useQuery({
    queryKey: activitiesKeys.list(filters),
    queryFn: () => activitiesApi.list(filters),
  })
}

// Get single activity
export function useActivity(id: number) {
  return useQuery({
    queryKey: activitiesKeys.detail(id),
    queryFn: () => activitiesApi.get(id),
    enabled: !!id, // Only fetch if ID exists
  })
}

// Get activity participants
export function useActivityParticipants(id: number) {
  return useQuery({
    queryKey: activitiesKeys.participants(id),
    queryFn: () => activitiesApi.getParticipants(id),
    enabled: !!id,
  })
}

// Create activity
export function useCreateActivity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: any) => activitiesApi.create(data),
    onSuccess: (result) => {
      // Track analytics
      trackEvent('activity_create', {
        activity_id: result?.id,
        sport_type: result?.sportType
      })
      // Invalidate all activity lists
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}

// Update activity
export function useUpdateActivity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data, notifyParticipants = false }: { id: number; data: any; notifyParticipants?: boolean }) =>
      activitiesApi.update(id, data, notifyParticipants),
    onSuccess: (_, { id }) => {
      // Invalidate specific activity and lists
      queryClient.invalidateQueries({ queryKey: activitiesKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}

// Delete activity
export function useDeleteActivity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, notifyParticipants = false }: { id: number; notifyParticipants?: boolean }) =>
      activitiesApi.delete(id, notifyParticipants),
    onSuccess: () => {
      // Invalidate lists (detail is now 404, no need to invalidate)
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}

// Join activity
export function useJoinActivity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => activitiesApi.join(id),
    onMutate: async (id) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: activitiesKeys.lists() })
      await queryClient.cancelQueries({ queryKey: activitiesKeys.detail(id) })

      // Snapshot previous values
      const previousLists = queryClient.getQueriesData({ queryKey: activitiesKeys.lists() })
      const previousDetail = queryClient.getQueryData(activitiesKeys.detail(id))

      // Optimistically update lists
      queryClient.setQueriesData({ queryKey: activitiesKeys.lists() }, (old: any) => {
        if (!old) return old
        return old.map((activity: any) =>
          activity.id === id ? { ...activity, isJoined: true } : activity
        )
      })

      // Optimistically update detail
      queryClient.setQueryData(activitiesKeys.detail(id), (old: any) => {
        if (!old) return old
        return { ...old, isJoined: true }
      })

      return { previousLists, previousDetail }
    },
    onError: (err, id, context: any) => {
      // Rollback on error
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]: [any, any]) => {
          queryClient.setQueryData(queryKey, data)
        })
      }
      if (context?.previousDetail) {
        queryClient.setQueryData(activitiesKeys.detail(id), context.previousDetail)
      }
    },
    onSettled: (_, __, id) => {
      // Always refetch after mutation settles
      queryClient.invalidateQueries({ queryKey: activitiesKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.participants(id) })
    },
    onSuccess: (_, id) => {
      // Track analytics
      trackEvent('activity_join', { activity_id: id })
    },
  })
}

// Leave activity
export function useLeaveActivity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => activitiesApi.leave(id),
    onSuccess: (_, id) => {
      // Track analytics
      trackEvent('activity_cancel', { activity_id: id })
      // Invalidate activity details and lists
      queryClient.invalidateQueries({ queryKey: activitiesKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.participants(id) })
    },
  })
}

// Confirm attendance for past activity
export function useConfirmActivity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, attended }: { id: number; attended: boolean }) =>
      activitiesApi.confirm(id, attended),
    onSuccess: (_, { id, attended }) => {
      // Track analytics
      trackEvent('activity_attend', { activity_id: id, attended })
      // Invalidate activity details and lists
      queryClient.invalidateQueries({ queryKey: activitiesKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}
