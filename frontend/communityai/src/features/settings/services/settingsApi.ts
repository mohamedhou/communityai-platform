import { API_BASE_URL } from '../../../lib/env'
import type { ChangePasswordRequest, ChangePasswordResponse, UserSettings, UserSettingsUpdate } from '../types/settings'

async function request<T>(path: string, accessToken: string, options: { method?: 'GET' | 'PATCH' | 'POST'; body?: unknown } = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    credentials: 'include',
    body: options.body ? JSON.stringify(options.body) : undefined,
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(payload.detail || 'Request failed')
  }
  return response.json() as Promise<T>
}

export function getSettings(accessToken: string): Promise<UserSettings> {
  return request<UserSettings>('/api/v1/settings', accessToken)
}

export function updateSettings(accessToken: string, payload: UserSettingsUpdate): Promise<UserSettings> {
  return request<UserSettings>('/api/v1/settings', accessToken, { method: 'PATCH', body: payload })
}

export function changePassword(accessToken: string, payload: ChangePasswordRequest): Promise<ChangePasswordResponse> {
  return request<ChangePasswordResponse>('/api/v1/settings/change-password', accessToken, { method: 'POST', body: payload })
}