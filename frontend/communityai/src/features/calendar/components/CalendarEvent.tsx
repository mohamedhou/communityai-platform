import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/hooks/useAuth'
import type { Post } from '../../posts/types/post'
import type { SocialAccount } from '../../social-accounts/types/social'

interface CalendarEventProps {
  post: Post
  socialAccounts?: SocialAccount[]
  onDragStart?: (e: React.DragEvent<HTMLDivElement>, post: Post) => void
}

export function CalendarEvent({
  post,
  socialAccounts = [],
  onDragStart,
}: CalendarEventProps) {
  const navigate = useNavigate()
  const { user } = useAuth()

  // Find social account
  const account = socialAccounts.find((a) => a.id === post.social_account_id)
  const platform = (account?.platform || 'social').toLowerCase()
  const accountName = account?.account_name || `Account #${post.social_account_id}`

  // Format event time
  const timeStr = (() => {
    const raw = post.scheduled_at || post.published_at || post.created_at
    if (!raw) return ''
    const d = new Date(raw)
    const hh = d.getHours().toString().padStart(2, '0')
    const mm = d.getMinutes().toString().padStart(2, '0')
    return `${hh}:${mm}`
  })()

  // Draggable ONLY if status is SCHEDULED and not pending/rejected in approval
  const isDraggable =
    post.status === 'SCHEDULED' &&
    post.approval_status !== 'PENDING' &&
    post.approval_status !== 'REJECTED' &&
    !(user?.role === 'COMMUNITY_MANAGER' && post.approval_status !== 'APPROVED')

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
    if (!isDraggable) {
      e.preventDefault()
      return
    }
    e.dataTransfer.setData('application/json', JSON.stringify(post))
    e.dataTransfer.effectAllowed = 'move'
    if (onDragStart) {
      onDragStart(e, post)
    }
  }

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    // Open post edit page
    navigate(`/posts/${post.id}/edit`)
  }

  return (
    <div
      className={`calendar-event-card status-${post.status.toLowerCase()} ${isDraggable ? 'is-draggable' : 'is-static'}`}
      draggable={isDraggable}
      onDragStart={handleDragStart}
      onClick={handleClick}
      title={`Click to edit. ${isDraggable ? 'Drag to move date.' : user?.role === 'COMMUNITY_MANAGER' && post.approval_status !== 'APPROVED' ? 'Approval required before scheduling or publishing.' : 'Cannot be moved.'}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          navigate(`/posts/${post.id}/edit`)
        }
      }}
    >
      <div className="calendar-event-top">
        {timeStr && <span className="calendar-event-time">{timeStr}</span>}

        <span className={`calendar-event-platform platform-${platform}`} title={`${accountName} (${platform})`}>
          {platform === 'linkedin' ? 'LinkedIn' : platform === 'facebook' ? 'Facebook' : platform === 'instagram' ? 'Instagram' : 'Meta'}
        </span>

        <span className={`calendar-event-status status-badge-${post.status.toLowerCase()}`}>
          {post.status}
        </span>

        {post.approval_status === 'PENDING' && (
          <span
            style={{
              fontSize: '0.68rem',
              padding: '1px 5px',
              borderRadius: '4px',
              background: '#fef3c7',
              color: '#92400e',
              fontWeight: 700,
            }}
            title="Pending Review"
          >
            ⏳
          </span>
        )}
        {post.approval_status === 'REJECTED' && (
          <span
            style={{
              fontSize: '0.68rem',
              padding: '1px 5px',
              borderRadius: '4px',
              background: '#fee2e2',
              color: '#991b1b',
              fontWeight: 700,
            }}
            title="Changes Requested / Rejected"
          >
            ✕
          </span>
        )}
        {post.approval_status === 'APPROVED' && (
          <span
            style={{
              fontSize: '0.68rem',
              padding: '1px 5px',
              borderRadius: '4px',
              background: '#dcfce7',
              color: '#166534',
              fontWeight: 700,
            }}
            title="Approved"
          >
            ✓
          </span>
        )}
      </div>

      <div className="calendar-event-content">
        {post.content}
      </div>

      {isDraggable && (
        <div className="calendar-drag-indicator" title="Drag to reschedule">
          ⋮⋮
        </div>
      )}
    </div>
  )
}
