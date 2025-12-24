import { useMutation, useQueryClient } from '@tanstack/react-query'
import { recurringApi } from '../api'
import { activitiesKeys } from './useActivities'

// Recurring update/cancel scope types
type RecurringUpdateScope = 'this_only' | 'this_and_following'
type RecurringCancelScope = 'this_only' | 'entire_series'

// Create recurring series (generates all activity instances)
export function useCreateRecurringSeries() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: any) => recurringApi.create(data),
    onSuccess: () => {
      // Invalidate all activity lists
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}

// Update recurring activity
export function useUpdateRecurring() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      activityId,
      scope,
      data
    }: {
      activityId: string
      scope: RecurringUpdateScope
      data: any
    }) => recurringApi.update(activityId, scope, data),
    onSuccess: () => {
      // Invalidate all activity lists since multiple activities may be updated
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}

// Cancel recurring activity
export function useCancelRecurring() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      activityId,
      scope
    }: {
      activityId: string
      scope: RecurringCancelScope
    }) => recurringApi.cancel(activityId, scope),
    onSuccess: () => {
      // Invalidate all activity lists since multiple activities may be cancelled
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    },
  })
}
