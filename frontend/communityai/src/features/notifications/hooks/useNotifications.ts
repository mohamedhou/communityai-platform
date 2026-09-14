import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import {
  deleteNotification,
  getNotifications,
  getUnreadNotificationCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '../services/notificationApi'
import type { NotificationFilters } from '../types/notification'

export const notificationListKey = ['notifications'] as const
export const notificationUnreadKey = ['notifications', 'unread-count'] as const

export function useNotifications(filters: NotificationFilters = {}) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: [...notificationListKey, filters],
    queryFn: () => getNotifications(accessToken!, filters),
    enabled: Boolean(accessToken),
  })
}

export function useUnreadNotificationCount() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: notificationUnreadKey,
    queryFn: () => getUnreadNotificationCount(accessToken!),
    enabled: Boolean(accessToken),
    refetchInterval: 30_000,
  })
}

export function useMarkNotificationRead() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, isRead = true }: { id: number; isRead?: boolean }) =>
      markNotificationRead(accessToken!, id, isRead),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationListKey })
      queryClient.invalidateQueries({ queryKey: notificationUnreadKey })
    },
  })
}

export function useMarkAllNotificationsRead() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => markAllNotificationsRead(accessToken!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationListKey })
      queryClient.invalidateQueries({ queryKey: notificationUnreadKey })
    },
  })
}

export function useDeleteNotification() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteNotification(accessToken!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationListKey })
      queryClient.invalidateQueries({ queryKey: notificationUnreadKey })
    },
  })
}