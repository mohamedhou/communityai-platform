export type WorkspaceRole = 'OWNER' | 'ADMIN' | 'COMMUNITY_MANAGER' | 'CLIENT'
export type MembershipStatus = 'ACTIVE' | 'INACTIVE'
export type InvitationStatus = 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'REVOKED'

export interface WorkspaceMember {
  id: number
  workspace_id: number
  user_id: number
  name: string
  email: string
  role: WorkspaceRole
  status: MembershipStatus
  joined_at: string | null
  created_at: string
}

export interface WorkspaceInvitation {
  id: number
  email: string
  role: WorkspaceRole
  expires_at: string
  accepted_at: string | null
  revoked_at: string | null
  created_at: string
  status: InvitationStatus
  invitation_url?: string | null
}

export interface WorkspaceInvitationPreview {
  workspace_name: string
  email: string
  role: WorkspaceRole
  expires_at: string
  status: InvitationStatus
}

export interface WorkspaceInvitationCreate {
  email: string
  role: WorkspaceRole
}

export interface WorkspaceRoleUpdate {
  role: WorkspaceRole
}

export interface WorkspaceMemberStatusUpdate {
  status: MembershipStatus
}
