import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { groupsApi, analyticsApi } from '../api'

// Helper to track analytics events (fire and forget)
const trackEvent = (eventName: string, params?: Record<string, any>) => {
  analyticsApi.trackEvent(eventName, params).catch(() => {})
}

// Query keys for groups
export const groupsKeys = {
  all: ['groups'] as const,
  lists: () => [...groupsKeys.all, 'list'] as const,
  list: (params: { clubId?: number | null; limit?: number; offset?: number }) =>
    [...groupsKeys.lists(), params] as const,
  details: () => [...groupsKeys.all, 'detail'] as const,
  detail: (id: number) => [...groupsKeys.details(), id] as const,
  members: (id: number) => [...groupsKeys.detail(id), 'members'] as const,
}

// List groups (optionally filtered by club)
export function useGroups(clubId: number | null = null, limit = 50, offset = 0) {
  return useQuery({
    queryKey: groupsKeys.list({ clubId, limit, offset }),
    queryFn: () => groupsApi.list(clubId, limit, offset),
  })
}

// Get single group
export function useGroup(id: number) {
  return useQuery({
    queryKey: groupsKeys.detail(id),
    queryFn: () => groupsApi.get(id),
    enabled: !!id,
  })
}

// Get group members
export function useGroupMembers(id: number) {
  return useQuery({
    queryKey: groupsKeys.members(id),
    queryFn: () => groupsApi.getMembers(id),
    enabled: !!id,
  })
}

// Create group
export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: any) => groupsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupsKeys.lists() })
    },
  })
}

// Update group
export function useUpdateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      groupsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: groupsKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: groupsKeys.lists() })
    },
  })
}

// Delete group
export function useDeleteGroup() {
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
    }) => groupsApi.delete(id, notifyMembers, deleteActivities),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupsKeys.lists() })
    },
  })
}

// Join group
export function useJoinGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => groupsApi.join(id),
    onSuccess: (_, id) => {
      // Track analytics
      trackEvent('group_join', { group_id: id })
      queryClient.invalidateQueries({ queryKey: groupsKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: groupsKeys.lists() })
      queryClient.invalidateQueries({ queryKey: groupsKeys.members(id) })
    },
  })
}
