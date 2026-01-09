import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clubsApi, analyticsApi } from '../api'

// Helper to track analytics events (fire and forget)
const trackEvent = (eventName: string, params?: Record<string, any>) => {
  analyticsApi.trackEvent(eventName, params).catch(() => {})
}

// Query keys for clubs
export const clubsKeys = {
  all: ['clubs'] as const,
  lists: () => [...clubsKeys.all, 'list'] as const,
  list: (params: { limit?: number; offset?: number }) => [...clubsKeys.lists(), params] as const,
  details: () => [...clubsKeys.all, 'detail'] as const,
  detail: (id: number) => [...clubsKeys.details(), id] as const,
  members: (id: number) => [...clubsKeys.detail(id), 'members'] as const,
}

// List clubs
export function useClubs(limit = 50, offset = 0) {
  return useQuery({
    queryKey: clubsKeys.list({ limit, offset }),
    queryFn: () => clubsApi.list(limit, offset),
  })
}

// Get single club
export function useClub(id: number) {
  return useQuery({
    queryKey: clubsKeys.detail(id),
    queryFn: () => clubsApi.get(id),
    enabled: !!id,
  })
}

// Get club members
export function useClubMembers(id: number) {
  return useQuery({
    queryKey: clubsKeys.members(id),
    queryFn: () => clubsApi.getMembers(id),
    enabled: !!id,
  })
}

// Create club
export function useCreateClub() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: any) => clubsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: clubsKeys.lists() })
    },
  })
}

// Update club
export function useUpdateClub() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      clubsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: clubsKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: clubsKeys.lists() })
    },
  })
}

// Delete club
export function useDeleteClub() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      notifyMembers = false,
      deleteActivities = true
    }: {
      id: number
      notifyMembers?: boolean
      deleteActivities?: boolean
    }) => clubsApi.delete(id, notifyMembers, deleteActivities),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: clubsKeys.lists() })
    },
  })
}

// Join club
export function useJoinClub() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => clubsApi.join(id),
    onSuccess: (_, id) => {
      // Track analytics
      trackEvent('club_join', { club_id: id })
      queryClient.invalidateQueries({ queryKey: clubsKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: clubsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: clubsKeys.members(id) })
    },
  })
}
