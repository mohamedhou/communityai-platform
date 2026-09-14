import { API_BASE_URL } from '../../../lib/env'
import type {
  Notification,
  NotificationFilters,
  NotificationListResponse,
  NotificationUnreadCountResponse,
} from '../types/notification'

const API_BASE = `${API_BASE_URL}/api/v1/notifications`

async function parseResponse<T>(response: Response, fallback: string): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: fallback }))
    throw new Error(error.detail || fallback)
  }
  return response.status === 204 ? (undefined as T) : response.json()
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` }
}

export async function getNotifications(
  token: string,
  filters: NotificationFilters = {},
): Promise<NotificationListResponse> {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined) params.set(key, String(value))
  }
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return parseResponse(
    await fetch(`${API_BASE}${suffix}`, { headers: authHeaders(token) }),
    'Impossible de charger les notifications',
  )
}

export async function getUnreadNotificationCount(token: string): Promise<NotificationUnreadCountResponse> {
  return parseResponse(
    await fetch(`${API_BASE}/unread-count`, { headers: authHeaders(token) }),
    'Impossible de charger le compteur de notifications',
  )
}

export async function markNotificationRead(token: string, id: number, isRead = true): Promise<Notification> {
  return parseResponse(
    await fetch(`${API_BASE}/${id}/read`, {
      method: 'PATCH',
      headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_read: isRead }),
    }),
    'Impossible de modifier la notification',
  )
}

export async function markAllNotificationsRead(token: string): Promise<{ success: boolean; marked_count: number }> {
  return parseResponse(
    await fetch(`${API_BASE}/read-all`, { method: 'PATCH', headers: authHeaders(token) }),
    'Impossible de marquer les notifications comme lues',
  )
}

export async function deleteNotification(token: string, id: number): Promise<void> {
  await parseResponse<void>(
    await fetch(`${API_BASE}/${id}`, { method: 'DELETE', headers: authHeaders(token) }),
    'Impossible de supprimer la notification',
  )
}