import { API_BASE_URL } from '../../../lib/env'
import type {
  WorkspaceInvitation,
  WorkspaceInvitationCreate,
  WorkspaceInvitationPreview,
  WorkspaceMember,
  WorkspaceRole,
  MembershipStatus,
} from '../types/workspace'

async function request<T>(
  path: string,
  accessToken?: string | null,
  options: { method?: 'GET' | 'PATCH' | 'POST' | 'DELETE'; body?: unknown } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    credentials: 'include',
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(payload.detail || 'Request failed')
  }

  if (response.status === 204) {
    return null as T
  }

  return response.json() as Promise<T>
}

export function listMembers(accessToken: string): Promise<WorkspaceMember[]> {
  return request<WorkspaceMember[]>('/api/v1/workspace/members', accessToken)
}

export function createInvitation(
  accessToken: string,
  payload: WorkspaceInvitationCreate
): Promise<WorkspaceInvitation> {
  return request<WorkspaceInvitation>('/api/v1/workspace/invitations', accessToken, {
    method: 'POST',
    body: payload,
  })
}

export function listInvitations(accessToken: string): Promise<WorkspaceInvitation[]> {
  return request<WorkspaceInvitation[]>('/api/v1/workspace/invitations', accessToken)
}

export function revokeInvitation(accessToken: string, invitationId: number): Promise<void> {
  return request<void>(`/api/v1/workspace/invitations/${invitationId}/revoke`, accessToken, {
    method: 'POST',
  })
}

export function updateMemberRole(
  accessToken: string,
  memberId: number,
  role: WorkspaceRole
): Promise<WorkspaceMember> {
  return request<WorkspaceMember>(`/api/v1/workspace/members/${memberId}/role`, accessToken, {
    method: 'PATCH',
    body: { role },
  })
}

export function updateMemberStatus(
  accessToken: string,
  memberId: number,
  status: MembershipStatus
): Promise<WorkspaceMember> {
  return request<WorkspaceMember>(`/api/v1/workspace/members/${memberId}/status`, accessToken, {
    method: 'PATCH',
    body: { status },
  })
}

export function removeMember(accessToken: string, memberId: number): Promise<void> {
  return request<void>(`/api/v1/workspace/members/${memberId}`, accessToken, {
    method: 'DELETE',
  })
}

export function previewInvitation(token: string): Promise<WorkspaceInvitationPreview> {
  return request<WorkspaceInvitationPreview>(`/api/v1/workspace/invitations/${token}`)
}

export function acceptInvitation(accessToken: string, token: string): Promise<WorkspaceMember> {
  return request<WorkspaceMember>(`/api/v1/workspace/invitations/${token}/accept`, accessToken, {
    method: 'POST',
  })
}
