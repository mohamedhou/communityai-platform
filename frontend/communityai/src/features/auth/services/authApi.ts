import { API_BASE_URL } from '../../../lib/env'
import type {
  AuthUser,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from '../types/auth'

async function request<T>(
  path: string,
  options: {
    method?: 'GET' | 'POST'
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

export function register(payload: RegisterRequest): Promise<AuthUser> {
  return request<AuthUser>('/api/v1/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function refresh(): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/auth/refresh', {
    method: 'POST',
    body: {},
  })
}

export function getMe(accessToken: string): Promise<AuthUser> {
  return request<AuthUser>('/api/v1/auth/me', {
    method: 'GET',
    accessToken,
  })
}

export function logout(): Promise<{ message: string }> {
  return request<{ message: string }>('/api/v1/auth/logout', {
    method: 'POST',
    body: {},
  })
}
