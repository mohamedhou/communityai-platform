import { API_BASE_URL } from '../../../lib/env'
import type { SocialAccount } from '../types/social'

async function request<T>(
  path: string,
  options: {
    method?: 'GET' | 'POST' | 'DELETE' | 'PATCH'
    body?: unknown
    accessToken?: string
  } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (options.accessToken) {
    headers.Authorization = `Bearer ${options.accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    credentials: 'include',
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    let detail = 'Request failed'
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) {
        detail = payload.detail
      }
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }

  // Handle empty bodies for DELETE/etc
  if (response.status === 204) {
    return {} as T
  }

  return response.json() as Promise<T>
}

export function getSocialAccounts(accessToken: string): Promise<SocialAccount[]> {
  return request<SocialAccount[]>('/api/v1/social-accounts', {
    method: 'GET',
    accessToken,
  })
}

export function getConnectUrl(
  accessToken: string,
  platform: string,
): Promise<{ url: string }> {
  return request<{ url: string }>(`/api/v1/social-accounts/${platform}/connect`, {
    method: 'GET',
    accessToken,
  })
}

export function disconnectSocialAccount(
  accessToken: string,
  accountId: number,
): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/v1/social-accounts/${accountId}`, {
    method: 'DELETE',
    accessToken,
  })
}

export function refreshSocialAccountToken(
  accessToken: string,
  accountId: number,
): Promise<SocialAccount> {
  return request<SocialAccount>(`/api/v1/social-accounts/${accountId}/refresh`, {
    method: 'POST',
    accessToken,
  })
}
