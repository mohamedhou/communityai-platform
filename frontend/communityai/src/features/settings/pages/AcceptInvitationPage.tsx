import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../../auth/hooks/useAuth'
import { useAcceptInvitation, useInvitationPreview } from '../hooks/useWorkspace'

const roleLabels: Record<string, string> = {
  OWNER: 'Workspace Owner',
  ADMIN: 'Administrator',
  COMMUNITY_MANAGER: 'Community Manager',
  CLIENT: 'Client Observer',
}

export function AcceptInvitationPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { user, accessToken } = useAuth()
  const { data: invitation, isLoading, isError, error } = useInvitationPreview(token || '')
  const acceptMutation = useAcceptInvitation()

  const [accepted, setAccepted] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="invitation-page-shell">
        <div className="invitation-card">
          <div className="invitation-loading">Loading invitation details...</div>
        </div>
      </div>
    )
  }

  if (isError || !invitation) {
    return (
      <div className="invitation-page-shell">
        <div className="invitation-card">
          <div className="invitation-icon-error">✕</div>
          <h2>Invalid Invitation</h2>
          <p className="invitation-text">
            {(error as Error)?.message || 'This invitation does not exist or has expired.'}
          </p>
          <Link to="/" className="btn btn-primary mt-4">
            Go to CommunityAI
          </Link>
        </div>
      </div>
    )
  }

  if (invitation.status === 'EXPIRED') {
    return (
      <div className="invitation-page-shell">
        <div className="invitation-card">
          <div className="invitation-icon-error">⏳</div>
          <h2>Invitation Expired</h2>
          <p className="invitation-text">
            This invitation to join <strong>{invitation.workspace_name}</strong> expired on{' '}
            {new Date(invitation.expires_at).toLocaleDateString()}. Please contact the workspace admin for a new link.
          </p>
          <Link to="/" className="btn btn-primary mt-4">
            Go to Home
          </Link>
        </div>
      </div>
    )
  }

  if (invitation.status === 'REVOKED') {
    return (
      <div className="invitation-page-shell">
        <div className="invitation-card">
          <div className="invitation-icon-error">⛔</div>
          <h2>Invitation Revoked</h2>
          <p className="invitation-text">
            This invitation was revoked by the workspace administrator.
          </p>
          <Link to="/" className="btn btn-primary mt-4">
            Go to Home
          </Link>
        </div>
      </div>
    )
  }

  if (invitation.status === 'ACCEPTED' || accepted) {
    return (
      <div className="invitation-page-shell">
        <div className="invitation-card">
          <div className="invitation-icon-success">✓</div>
          <h2>Welcome to {invitation.workspace_name}!</h2>
          <p className="invitation-text">
            You are now a member of the workspace with the role of{' '}
            <strong>{roleLabels[invitation.role] || invitation.role}</strong>.
          </p>
          <button
            type="button"
            className="btn btn-primary mt-4"
            onClick={() => navigate('/settings')}
          >
            Go to Workspace Settings
          </button>
        </div>
      </div>
    )
  }

  const isEmailMatch = user && user.email.toLowerCase() === invitation.email.toLowerCase()

  const handleAccept = () => {
    if (!token) return
    setErrorMessage(null)
    acceptMutation.mutate(token, {
      onSuccess: () => {
        setAccepted(true)
      },
      onError: (err: any) => {
        setErrorMessage(err.message || 'Failed to accept invitation.')
      },
    })
  }

  return (
    <div className="invitation-page-shell">
      <div className="invitation-card">
        <div className="invitation-badge">Workspace Invitation</div>
        <h2>Join {invitation.workspace_name}</h2>
        <p className="invitation-subtitle">
          You have been invited to collaborate on CommunityAI.
        </p>

        <div className="invitation-details-box">
          <div className="invitation-row">
            <span className="invitation-label">Invited email:</span>
            <span className="invitation-value">{invitation.email}</span>
          </div>
          <div className="invitation-row">
            <span className="invitation-label">Assigned role:</span>
            <span className="invitation-value badge-role-highlight">
              {roleLabels[invitation.role] || invitation.role}
            </span>
          </div>
          <div className="invitation-row">
            <span className="invitation-label">Valid until:</span>
            <span className="invitation-value">
              {new Date(invitation.expires_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {errorMessage && (
          <div className="alert-banner alert-error mt-4">
            <span>{errorMessage}</span>
          </div>
        )}

        {!accessToken ? (
          <div className="invitation-auth-prompt mt-6">
            <p className="text-sm text-secondary mb-4">
              Please sign in with <strong>{invitation.email}</strong> to accept this invitation.
            </p>
            <div className="invitation-actions-group">
              <Link
                to={`/login?redirect=/invitations/${token}`}
                className="btn btn-primary"
              >
                Sign In
              </Link>
              <Link
                to={`/register?email=${encodeURIComponent(invitation.email)}&redirect=/invitations/${token}`}
                className="btn btn-secondary"
              >
                Create Account
              </Link>
            </div>
          </div>
        ) : !isEmailMatch ? (
          <div className="alert-banner alert-error mt-6 text-left">
            <p className="font-semibold mb-1">Account Mismatch</p>
            <p className="text-sm">
              You are currently signed in as <strong>{user?.email}</strong>. This invitation was sent specifically to{' '}
              <strong>{invitation.email}</strong>. Please switch accounts to accept.
            </p>
          </div>
        ) : (
          <div className="mt-6">
            <button
              type="button"
              className="btn btn-primary btn-lg w-full"
              onClick={handleAccept}
              disabled={acceptMutation.isPending}
            >
              {acceptMutation.isPending ? 'Joining Workspace...' : 'Accept Invitation & Join'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
