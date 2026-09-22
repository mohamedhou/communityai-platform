import { useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import {
  useCreateInvitation,
  useRemoveMember,
  useRevokeInvitation,
  useUpdateMemberRole,
  useUpdateMemberStatus,
  useWorkspaceInvitations,
  useWorkspaceMembers,
} from '../hooks/useWorkspace'
import type { WorkspaceMember, WorkspaceRole } from '../types/workspace'

const roleLabels: Record<WorkspaceRole, string> = {
  OWNER: 'Owner',
  ADMIN: 'Admin',
  COMMUNITY_MANAGER: 'Community Manager',
  CLIENT: 'Client (Read-only)',
}

const roleDescriptions: Record<WorkspaceRole, string> = {
  OWNER: 'Complete workspace ownership, billing, and member management.',
  ADMIN: 'Can invite and manage team members and publish content.',
  COMMUNITY_MANAGER: 'Can create and schedule posts, reply in inbox, view analytics.',
  CLIENT: 'Read-only access to calendar, posts, and analytics.',
}

export function TeamSettings() {
  const { user } = useAuth()
  const { data: members, isLoading: membersLoading } = useWorkspaceMembers()
  const { data: invitations, isLoading: invitesLoading } = useWorkspaceInvitations()

  const createInviteMutation = useCreateInvitation()
  const revokeInviteMutation = useRevokeInvitation()
  const updateRoleMutation = useUpdateMemberRole()
  const updateStatusMutation = useUpdateMemberStatus()
  const removeMemberMutation = useRemoveMember()

  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState<WorkspaceRole>('COMMUNITY_MANAGER')
  const [copiedToken, setCopiedToken] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [memberToRemove, setMemberToRemove] = useState<WorkspaceMember | null>(null)

  // Current user membership in the workspace
  const currentMember = members?.find((m) => m.user_id === user?.id)
  const isManager = currentMember?.role === 'OWNER' || currentMember?.role === 'ADMIN'

  const handleSendInvite = (e: React.FormEvent) => {
    e.preventDefault()
    setStatusMessage(null)
    createInviteMutation.mutate(
      { email: inviteEmail.trim().toLowerCase(), role: inviteRole },
      {
        onSuccess: (invitation) => {
          setStatusMessage({
            type: 'success',
            text: `Invitation sent to ${invitation.email}.`,
          })
          setInviteEmail('')
          setIsInviteModalOpen(false)
        },
        onError: (err: any) => {
          setStatusMessage({
            type: 'error',
            text: err.message || 'Failed to send invitation',
          })
        },
      }
    )
  }

  const handleCopyLink = (invitationUrl: string | null | undefined, id: number) => {
    if (!invitationUrl) return
    const fullUrl = `${window.location.origin}${invitationUrl}`
    navigator.clipboard.writeText(fullUrl)
    setCopiedToken(String(id))
    setTimeout(() => setCopiedToken(null), 3000)
  }

  const handleRevoke = (id: number) => {
    setStatusMessage(null)
    revokeInviteMutation.mutate(id, {
      onSuccess: () => {
        setStatusMessage({ type: 'success', text: 'Invitation revoked successfully.' })
      },
      onError: (err: any) => {
        setStatusMessage({ type: 'error', text: err.message || 'Failed to revoke invitation.' })
      },
    })
  }

  const handleRoleChange = (member: WorkspaceMember, newRole: WorkspaceRole) => {
    setStatusMessage(null)
    updateRoleMutation.mutate(
      { memberId: member.id, role: newRole },
      {
        onSuccess: () => {
          setStatusMessage({ type: 'success', text: `Updated role for ${member.name}.` })
        },
        onError: (err: any) => {
          setStatusMessage({ type: 'error', text: err.message || 'Failed to update role.' })
        },
      }
    )
  }

  const handleStatusToggle = (member: WorkspaceMember) => {
    setStatusMessage(null)
    const nextStatus = member.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
    updateStatusMutation.mutate(
      { memberId: member.id, status: nextStatus },
      {
        onSuccess: () => {
          setStatusMessage({
            type: 'success',
            text: `${member.name} membership is now ${nextStatus.toLowerCase()}.`,
          })
        },
        onError: (err: any) => {
          setStatusMessage({ type: 'error', text: err.message || 'Failed to update member status.' })
        },
      }
    )
  }

  const handleConfirmRemove = () => {
    if (!memberToRemove) return
    setStatusMessage(null)
    removeMemberMutation.mutate(memberToRemove.id, {
      onSuccess: () => {
        setStatusMessage({ type: 'success', text: `${memberToRemove.name} removed from workspace.` })
        setMemberToRemove(null)
      },
      onError: (err: any) => {
        setStatusMessage({ type: 'error', text: err.message || 'Failed to remove member.' })
      },
    })
  }

  return (
    <div className="team-settings-container">
      <div className="team-settings-header">
        <div>
          <h2>Team & Collaboration</h2>
          <p className="team-settings-subtitle">
            Manage agency team members, client observers, and invitations for this workspace.
          </p>
        </div>
        {isManager && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              setIsInviteModalOpen(true)
              setStatusMessage(null)
            }}
          >
            + Invite Member
          </button>
        )}
      </div>

      {statusMessage && (
        <div className={`alert-banner alert-${statusMessage.type}`}>
          <span>{statusMessage.text}</span>
          <button
            type="button"
            className="alert-close-btn"
            onClick={() => setStatusMessage(null)}
            aria-label="Close"
          >
            ✕
          </button>
        </div>
      )}

      {/* Members Section */}
      <div className="team-card">
        <div className="team-card-header">
          <h3>Active Members ({members?.length ?? 0})</h3>
        </div>

        {membersLoading ? (
          <div className="team-loading">Loading members...</div>
        ) : (
          <div className="table-responsive">
            <table className="team-table">
              <thead>
                <tr>
                  <th>Member</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                  {isManager && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {members?.map((member) => {
                  const isOwner = member.role === 'OWNER'
                  const isSelf = member.user_id === user?.id
                  const canEdit = isManager && !isOwner && (!isSelf || currentMember?.role === 'OWNER')

                  return (
                    <tr key={member.id}>
                      <td>
                        <div className="member-info">
                          <div className="member-avatar">
                            {member.name
                              .split(' ')
                              .map((n) => n[0])
                              .slice(0, 2)
                              .join('')
                              .toUpperCase()}
                          </div>
                          <div>
                            <div className="member-name">
                              {member.name} {isSelf && <span className="badge-self">You</span>}
                            </div>
                            <div className="member-email">{member.email}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        {isManager && !isOwner && !isSelf ? (
                          <select
                            className="role-select"
                            value={member.role}
                            disabled={updateRoleMutation.isPending}
                            onChange={(e) => handleRoleChange(member, e.target.value as WorkspaceRole)}
                          >
                            {currentMember?.role === 'OWNER' && <option value="OWNER">Owner</option>}
                            <option value="ADMIN">Admin</option>
                            <option value="COMMUNITY_MANAGER">Community Manager</option>
                            <option value="CLIENT">Client</option>
                          </select>
                        ) : (
                          <span className={`badge-role role-${member.role.toLowerCase()}`}>
                            {roleLabels[member.role]}
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`badge-status status-${member.status.toLowerCase()}`}>
                          {member.status}
                        </span>
                      </td>
                      <td>
                        <span className="member-date">
                          {member.joined_at
                            ? new Date(member.joined_at).toLocaleDateString()
                            : new Date(member.created_at).toLocaleDateString()}
                        </span>
                      </td>
                      {isManager && (
                        <td>
                          <div className="member-actions">
                            {canEdit && !isSelf && (
                              <>
                                <button
                                  type="button"
                                  className="btn-link"
                                  onClick={() => handleStatusToggle(member)}
                                  disabled={updateStatusMutation.isPending}
                                  title={member.status === 'ACTIVE' ? 'Deactivate member' : 'Activate member'}
                                >
                                  {member.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                                </button>
                                <button
                                  type="button"
                                  className="btn-link-danger"
                                  onClick={() => setMemberToRemove(member)}
                                  disabled={removeMemberMutation.isPending}
                                  title="Remove member from workspace"
                                >
                                  Remove
                                </button>
                              </>
                            )}
                            {isOwner && <span className="action-note">Workspace Owner</span>}
                            {isSelf && !isOwner && <span className="action-note">Your account</span>}
                          </div>
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invitations Section */}
      {isManager && (
        <div className="team-card mt-6">
          <div className="team-card-header">
            <h3>Pending & Recent Invitations ({invitations?.length ?? 0})</h3>
          </div>

          {invitesLoading ? (
            <div className="team-loading">Loading invitations...</div>
          ) : !invitations || invitations.length === 0 ? (
            <div className="empty-state">No invitations sent yet.</div>
          ) : (
            <div className="table-responsive">
              <table className="team-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Expires</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {invitations.map((inv) => (
                    <tr key={inv.id}>
                      <td className="font-medium">{inv.email}</td>
                      <td>
                        <span className={`badge-role role-${inv.role.toLowerCase()}`}>
                          {roleLabels[inv.role]}
                        </span>
                      </td>
                      <td>
                        <span className="member-date">
                          {new Date(inv.expires_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td>
                        <span className={`badge-status status-${inv.status.toLowerCase()}`}>
                          {inv.status}
                        </span>
                      </td>
                      <td>
                        <div className="invitation-actions">
                          {inv.status === 'PENDING' && (
                            <>
                              {inv.invitation_url && (
                                <button
                                  type="button"
                                  className="btn-link"
                                  onClick={() => handleCopyLink(inv.invitation_url, inv.id)}
                                >
                                  {copiedToken === String(inv.id) ? '✓ Copied!' : 'Copy Link'}
                                </button>
                              )}
                              <button
                                type="button"
                                className="btn-link-danger"
                                onClick={() => handleRevoke(inv.id)}
                                disabled={revokeInviteMutation.isPending}
                              >
                                Revoke
                              </button>
                            </>
                          )}
                          {inv.status !== 'PENDING' && (
                            <span className="action-note">{inv.status.toLowerCase()}</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Invite Member Modal */}
      {isInviteModalOpen && (
        <div className="modal-backdrop" onClick={() => setIsInviteModalOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Invite Team Member</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setIsInviteModalOpen(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSendInvite}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="invite-email">Member Email</label>
                  <input
                    id="invite-email"
                    type="email"
                    required
                    placeholder="colleague@agency.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="form-control"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="invite-role">Workspace Role</label>
                  <select
                    id="invite-role"
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as WorkspaceRole)}
                    className="form-control"
                  >
                    <option value="COMMUNITY_MANAGER">Community Manager</option>
                    <option value="ADMIN">Admin</option>
                    <option value="CLIENT">Client (Read-only)</option>
                  </select>
                  <p className="form-hint">{roleDescriptions[inviteRole]}</p>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsInviteModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={createInviteMutation.isPending || !inviteEmail.trim()}
                >
                  {createInviteMutation.isPending ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirm Remove Member Modal */}
      {memberToRemove && (
        <div className="modal-backdrop" onClick={() => setMemberToRemove(null)}>
          <div className="modal-dialog modal-dialog-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Remove Team Member</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setMemberToRemove(null)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to remove <strong>{memberToRemove.name}</strong> ({memberToRemove.email})
                from this workspace?
              </p>
              <p className="modal-warning">
                They will lose all access to workspace social accounts, scheduled posts, and analytics.
              </p>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setMemberToRemove(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleConfirmRemove}
                disabled={removeMemberMutation.isPending}
              >
                {removeMemberMutation.isPending ? 'Removing...' : 'Remove Member'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
