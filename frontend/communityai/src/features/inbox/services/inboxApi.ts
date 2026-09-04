import { API_BASE_URL } from '../../../lib/env'
import type {
  InboxFiltersState,
  InboxListResponse,
  InboxMessage,
  InboxSuggestReplyRequest,
  InboxUnreadCountResponse,
} from '../types/inbox'

const API_BASE = `${API_BASE_URL}/api/v1/inbox`

export async function getInboxMessages(
  token: string,
  filters?: InboxFiltersState,
  limit = 50,
  offset = 0,
): Promise<InboxListResponse> {
  const params = new URLSearchParams()
  params.append('limit', limit.toString())
  params.append('offset', offset.toString())

  if (filters?.type && filters.type !== 'ALL') {
    params.append('type', filters.type)
  }
  if (filters?.platform && filters.platform !== 'ALL') {
    params.append('platform', filters.platform)
  }
  if (filters?.sentiment && filters.sentiment !== 'ALL') {
    params.append('sentiment', filters.sentiment)
  }
  if (filters?.status === 'UNREAD') {
    params.append('is_read', 'false')
  } else if (filters?.status === 'READ') {
    params.append('is_read', 'true')
  } else if (filters?.status === 'RESOLVED') {
    params.append('is_resolved', 'true')
  }
  if (filters?.search && filters.search.trim()) {
    params.append('search', filters.search.trim())
  }

  const res = await fetch(`${API_BASE}?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch interactions' }))
    throw new Error(err.detail || 'Failed to fetch interactions')
  }
  return res.json()
}

export async function getInboxUnreadCount(token: string): Promise<InboxUnreadCountResponse> {
  const res = await fetch(`${API_BASE}/unread-count`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch unread count' }))
    throw new Error(err.detail || 'Failed to fetch unread count')
  }
  return res.json()
}

export async function getInboxMessage(token: string, messageId: number): Promise<InboxMessage> {
  const res = await fetch(`${API_BASE}/${messageId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch interaction details' }))
    throw new Error(err.detail || 'Failed to fetch interaction details')
  }
  return res.json()
}

export async function markInboxMessageRead(
  token: string,
  messageId: number,
  isRead = true,
): Promise<InboxMessage> {
  const res = await fetch(`${API_BASE}/${messageId}/read`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_read: isRead }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update read status' }))
    throw new Error(err.detail || 'Failed to update read status')
  }
  return res.json()
}

export async function markInboxMessageResolved(
  token: string,
  messageId: number,
  isResolved = true,
): Promise<InboxMessage> {
  const res = await fetch(`${API_BASE}/${messageId}/resolve`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_resolved: isResolved }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update resolve status' }))
    throw new Error(err.detail || 'Failed to update resolve status')
  }
  return res.json()
}

export async function suggestInboxReply(
  token: string,
  messageId: number,
  payload?: InboxSuggestReplyRequest,
): Promise<{ content: string }> {
  const res = await fetch(`${API_BASE}/${messageId}/suggest-reply`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload || {}),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate AI reply' }))
    throw new Error(err.detail || 'Failed to generate AI reply')
  }
  return res.json()
}

export async function sendInboxReply(
  token: string,
  messageId: number,
  content: string,
): Promise<InboxMessage> {
  const res = await fetch(`${API_BASE}/${messageId}/reply`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to send reply' }))
    throw new Error(err.detail || 'Failed to send reply')
  }
  return res.json()
}

export async function seedMockInboxMessages(token: string): Promise<InboxMessage[]> {
  const res = await fetch(`${API_BASE}/seed-mock`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to seed mock interactions' }))
    throw new Error(err.detail || 'Failed to seed mock interactions')
  }
  return res.json()
}
