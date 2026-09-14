import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import * as settingsApi from '../services/settingsApi'
import type { ChangePasswordRequest, UserSettingsUpdate } from '../types/settings'

export const settingsQueryKey = ['settings'] as const

export function useSettings() {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: settingsQueryKey,
    queryFn: () => settingsApi.getSettings(accessToken!),
    enabled: Boolean(accessToken),
  })
}

export function useUpdateSettings() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UserSettingsUpdate) => settingsApi.updateSettings(accessToken!, payload),
    onSuccess: (settings) => {
      queryClient.setQueryData(settingsQueryKey, settings)
      void queryClient.invalidateQueries({ queryKey: settingsQueryKey })
    },
  })
}

export function useChangePassword() {
  const { accessToken } = useAuth()
  return useMutation({
    mutationFn: (payload: ChangePasswordRequest) => settingsApi.changePassword(accessToken!, payload),
  })
}