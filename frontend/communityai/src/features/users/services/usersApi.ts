import { API_BASE_URL } from '../../../lib/env'
import type { AuthUser, UserRole } from '../../auth/types/auth'
import type {
  ChangePasswordRequest,
  ProfileUpdateRequest,
} from '../types/users'

async function request<T>(
  path: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'PATCH'
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

  return response.json() as Promise<T>
}

export function updateProfile(
  accessToken: string,
  payload: ProfileUpdateRequest,
): Promise<AuthUser> {
  return request<AuthUser>('/api/v1/users/me', {
    method: 'PUT',
    body: payload,
    accessToken,
  })
}

export function changePassword(
  accessToken: string,
  payload: ChangePasswordRequest,
): Promise<{ message: string }> {
  return request<{ message: string }>('/api/v1/users/me/change-password', {
    method: 'POST',
    body: payload,
    accessToken,
  })
}

export function getUsers(accessToken: string): Promise<AuthUser[]> {
  return request<AuthUser[]>('/api/v1/users', {
    method: 'GET',
    accessToken,
  })
}

export function getUser(accessToken: string, userId: number): Promise<AuthUser> {
  return request<AuthUser>(`/api/v1/users/${userId}`, {
    method: 'GET',
    accessToken,
  })
}

export function updateUser(
  accessToken: string,
  userId: number,
  payload: ProfileUpdateRequest,
): Promise<AuthUser> {
  return request<AuthUser>(`/api/v1/users/${userId}`, {
    method: 'PUT',
    body: payload,
    accessToken,
  })
}

export function updateUserStatus(
  accessToken: string,
  userId: number,
  is_active: boolean,
): Promise<AuthUser> {
  return request<AuthUser>(`/api/v1/users/${userId}/status`, {
    method: 'PATCH',
    body: { is_active },
    accessToken,
  })
}

export function updateUserRole(
  accessToken: string,
  userId: number,
  role: UserRole,
): Promise<AuthUser> {
  return request<AuthUser>(`/api/v1/users/${userId}/role`, {
    method: 'PATCH',
    body: { role },
    accessToken,
  })
}
