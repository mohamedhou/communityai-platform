import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { useAuth } from '../../auth/hooks/useAuth'
import * as postApi from '../services/postApi'
import { getSocialAccounts } from '../../social-accounts/services/socialApi'
import type { Post } from '../types/post'

export function ReviewQueuePage() {
  const { accessToken, user } = useAuth()
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<'queue' | 'history'>('queue')
  const [rejectingPost, setRejectingPost] = useState<Post | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)

  // Fetch queue
  const {
    data: queuePosts,
    isLoading: queueLoading,
    error: queueError,
  } = useQuery({
    queryKey: ['posts-review-queue'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.getReviewQueue(accessToken)
    },
    enabled: !!accessToken,
  })

  // Fetch history
  const {
    data: historyPosts,
    isLoading: historyLoading,
    error: historyError,
  } = useQuery({
    queryKey: ['posts-review-history'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.getReviewHistory(accessToken)
    },
    enabled: !!accessToken,
  })

  // Fetch social accounts
  const { data: accounts } = useQuery({
    queryKey: ['social-accounts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getSocialAccounts(accessToken)
    },
    enabled: !!accessToken,
  })

  const getAccountInfo = (accountId: number) => {
    const acc = accounts?.find((a) => a.id === accountId)
    if (!acc) return { name: `Account #${accountId}`, platform: 'unknown', avatar: '' }
    return {
      name: acc.account_name,
      platform: acc.platform,
      avatar: acc.profile_image_url,
    }
  }

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (postId: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.approvePost(accessToken, postId)
    },
    onSuccess: () => {
      setActionError(null)
      void queryClient.invalidateQueries({ queryKey: ['posts-review-queue'] })
      void queryClient.invalidateQueries({ queryKey: ['posts-review-history'] })
      void queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
    onError: (err: any) => {
      setActionError(err.message || 'Failed to approve post')
    },
  })

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ postId, reason }: { postId: number; reason: string }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.rejectPost(accessToken, postId, reason)
    },
    onSuccess: () => {
      setActionError(null)
      setRejectingPost(null)
      setRejectionReason('')
      void queryClient.invalidateQueries({ queryKey: ['posts-review-queue'] })
      void queryClient.invalidateQueries({ queryKey: ['posts-review-history'] })
      void queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
    onError: (err: any) => {
      setActionError(err.message || 'Failed to reject post')
    },
  })

  const handleOpenRejectModal = (post: Post) => {
    setRejectingPost(post)
    setRejectionReason('')
    setActionError(null)
  }

  const handleConfirmReject = (e: React.FormEvent) => {
    e.preventDefault()
    if (!rejectingPost) return
    if (!rejectionReason.trim()) {
      setActionError('A rejection reason is required.')
      return
    }
    rejectMutation.mutate({
      postId: rejectingPost.id,
      reason: rejectionReason.trim(),
    })
  }

  const isReviewer = user?.role === 'ADMIN'

  return (
    <main className="page-shell">
      <div className="social-container">
        {/* Header */}
        <div
          className="posts-header-row"
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Link
                to="/posts"
                style={{
                  color: '#2563eb',
                  textDecoration: 'none',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                }}
              >
                ← Back to Publications
              </Link>
            </div>
            <h1>Content Approval & Review Queue</h1>
            <p className="page-subtitle">
              Collaborative editorial workflow. Review, approve, or reject draft publications.
            </p>
          </div>
        </div>

        {/* Reviewer Role Notice */}
        {!isReviewer && (
          <div
            style={{
              background: '#eff6ff',
              border: '1px solid #bfdbfe',
              color: '#1e40af',
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '0.9rem',
            }}
          >
            ℹ️ You are viewing the queue as <strong>{user?.role || 'Guest'}</strong>. Only workspace Owners and Admins have permission to approve or reject content.
          </div>
        )}

        {/* Global Error Callout */}
        {actionError && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '0.95rem',
            }}
          >
            <strong>Error:</strong> {actionError}
          </div>
        )}

        {/* Tabs */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            borderBottom: '2px solid #e5e7eb',
            marginBottom: '24px',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('queue')}
            style={{
              padding: '10px 18px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'queue' ? '2px solid #2563eb' : '2px solid transparent',
              color: activeTab === 'queue' ? '#2563eb' : '#6b7280',
              fontWeight: 600,
              fontSize: '0.95rem',
              cursor: 'pointer',
              marginBottom: '-2px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            Pending Review
            {queuePosts && queuePosts.length > 0 && (
              <span
                style={{
                  background: '#f59e0b',
                  color: 'white',
                  borderRadius: '12px',
                  padding: '2px 8px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                }}
              >
                {queuePosts.length}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            style={{
              padding: '10px 18px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'history' ? '2px solid #2563eb' : '2px solid transparent',
              color: activeTab === 'history' ? '#2563eb' : '#6b7280',
              fontWeight: 600,
              fontSize: '0.95rem',
              cursor: 'pointer',
              marginBottom: '-2px',
            }}
          >
            Review History
          </button>
        </div>

        {/* Tab 1: Pending Queue */}
        {activeTab === 'queue' && (
          <div>
            {queueLoading ? (
              <div className="social-loading">Loading pending queue...</div>
            ) : queueError ? (
              <div className="social-error-page">
                Failed to load review queue: {(queueError as Error).message}
              </div>
            ) : queuePosts && queuePosts.length > 0 ? (
              <div className="channels-list">
                {queuePosts.map((post) => {
                  const acc = getAccountInfo(post.social_account_id)
                  const isPendingAction =
                    (approveMutation.isPending && approveMutation.variables === post.id) ||
                    (rejectMutation.isPending && rejectMutation.variables?.postId === post.id)

                  return (
                    <div
                      key={post.id}
                      className="channel-card"
                      style={{
                        flexDirection: 'column',
                        alignItems: 'stretch',
                        gap: '16px',
                        padding: '20px',
                        borderRadius: '12px',
                        border: '1px solid #fcd34d',
                        background: '#fffdfa',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                        }}
                      >
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          {acc.avatar ? (
                            <img
                              src={acc.avatar}
                              alt={acc.name}
                              className="channel-avatar"
                              style={{ width: '40px', height: '40px' }}
                            />
                          ) : (
                            <div
                              className={`channel-avatar-fallback ${acc.platform}`}
                              style={{ width: '40px', height: '40px' }}
                            >
                              {acc.name.charAt(0)}
                            </div>
                          )}
                          <div>
                            <h4 style={{ margin: 0 }}>{acc.name}</h4>
                            <span
                              className={`channel-platform-badge ${acc.platform}`}
                              style={{ position: 'static', display: 'inline-block', marginTop: '4px' }}
                            >
                              {acc.platform}
                            </span>
                          </div>
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '4px 10px',
                              borderRadius: '9999px',
                              fontSize: '0.8rem',
                              fontWeight: 700,
                              background: '#fef3c7',
                              color: '#92400e',
                              border: '1px solid #fde68a',
                            }}
                          >
                            ⏳ Pending Review
                          </span>
                          {post.submitted_for_review_at && (
                            <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>
                              Submitted: {new Date(post.submitted_for_review_at).toLocaleString()}
                            </div>
                          )}
                          {post.scheduled_at && (
                            <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
                              Target Schedule: {new Date(post.scheduled_at).toLocaleString()}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Content */}
                      <div
                        style={{
                          background: '#ffffff',
                          padding: '14px',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb',
                          whiteSpace: 'pre-wrap',
                          fontSize: '0.95rem',
                          color: '#1f2937',
                        }}
                      >
                        {post.content}
                      </div>

                      {/* Media preview */}
                      {post.media_url && (
                        <div style={{ fontSize: '0.85rem', color: '#2563eb' }}>
                          Media Attachment:{' '}
                          <a href={post.media_url} target="_blank" rel="noreferrer">
                            {post.media_url}
                          </a>
                        </div>
                      )}

                      {/* Action buttons */}
                      <div
                        style={{
                          display: 'flex',
                          gap: '10px',
                          justifyContent: 'flex-end',
                          borderTop: '1px solid #f3f4f6',
                          paddingTop: '12px',
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => approveMutation.mutate(post.id)}
                          disabled={isPendingAction}
                          style={{
                            background: '#16a34a',
                            color: 'white',
                            border: 'none',
                            padding: '8px 16px',
                            borderRadius: '6px',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          ✓ Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => handleOpenRejectModal(post)}
                          disabled={isPendingAction}
                          style={{
                            background: '#dc2626',
                            color: 'white',
                            border: 'none',
                            padding: '8px 16px',
                            borderRadius: '6px',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          ✕ Reject...
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="empty-channels">
                <p>No publications are currently waiting for review.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Review History */}
        {activeTab === 'history' && (
          <div>
            {historyLoading ? (
              <div className="social-loading">Loading review history...</div>
            ) : historyError ? (
              <div className="social-error-page">
                Failed to load review history: {(historyError as Error).message}
              </div>
            ) : historyPosts && historyPosts.length > 0 ? (
              <div className="channels-list">
                {historyPosts.map((post) => {
                  const acc = getAccountInfo(post.social_account_id)
                  const isApproved = post.approval_status === 'APPROVED'

                  return (
                    <div
                      key={post.id}
                      className="channel-card"
                      style={{
                        flexDirection: 'column',
                        alignItems: 'stretch',
                        gap: '14px',
                        padding: '18px',
                        borderRadius: '12px',
                        border: isApproved ? '1px solid #bbf7d0' : '1px solid #fecaca',
                        background: isApproved ? '#f0fdf4' : '#fff5f5',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                        }}
                      >
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          <span
                            className={`channel-platform-badge ${acc.platform}`}
                            style={{ position: 'static', display: 'inline-block' }}
                          >
                            {acc.platform}
                          </span>
                          <h4 style={{ margin: 0 }}>{acc.name}</h4>
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <span
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '4px 10px',
                              borderRadius: '9999px',
                              fontSize: '0.8rem',
                              fontWeight: 700,
                              background: isApproved ? '#dcfce7' : '#fee2e2',
                              color: isApproved ? '#166534' : '#991b1b',
                            }}
                          >
                            {isApproved ? '✓ APPROVED' : '✕ REJECTED'}
                          </span>
                          {post.reviewed_at && (
                            <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>
                              Reviewed: {new Date(post.reviewed_at).toLocaleString()}
                            </div>
                          )}
                        </div>
                      </div>

                      <div
                        style={{
                          background: '#ffffff',
                          padding: '12px',
                          borderRadius: '8px',
                          border: '1px solid #e5e7eb',
                          whiteSpace: 'pre-wrap',
                          fontSize: '0.9rem',
                        }}
                      >
                        {post.content}
                      </div>

                      {/* Rejection reason banner */}
                      {!isApproved && post.rejection_reason && (
                        <div
                          style={{
                            background: '#fef2f2',
                            border: '1px solid #fecaca',
                            color: '#b91c1c',
                            padding: '10px 14px',
                            borderRadius: '6px',
                            fontSize: '0.9rem',
                          }}
                        >
                          <strong>Reason for Rejection:</strong> {post.rejection_reason}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="empty-channels">
                <p>No reviewed publications in history yet.</p>
              </div>
            )}
          </div>
        )}

        {/* Rejection Modal Dialog */}
        {rejectingPost && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              padding: '16px',
            }}
          >
            <div
              style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                maxWidth: '500px',
                width: '100%',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
              }}
            >
              <h3 style={{ marginTop: 0, marginBottom: '8px', color: '#991b1b' }}>
                Reject Publication
              </h3>
              <p style={{ color: '#4b5563', fontSize: '0.9rem', marginBottom: '16px' }}>
                Please provide feedback explaining why this post was rejected. The author will be notified to revise and resubmit.
              </p>

              <form onSubmit={handleConfirmReject}>
                <div style={{ marginBottom: '16px' }}>
                  <label
                    htmlFor="rejection-reason-input"
                    style={{ display: 'block', fontWeight: 600, marginBottom: '6px' }}
                  >
                    Rejection Reason (Required)
                  </label>
                  <textarea
                    id="rejection-reason-input"
                    rows={4}
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="E.g., Please fix the typo in paragraph 2 and replace the banner image..."
                    required
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      border: '1px solid #d1d5db',
                      resize: 'vertical',
                      boxSizing: 'border-box',
                    }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setRejectingPost(null)
                      setRejectionReason('')
                    }}
                    disabled={rejectMutation.isPending}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      border: '1px solid #d1d5db',
                      background: '#f9fafb',
                      cursor: 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={rejectMutation.isPending || !rejectionReason.trim()}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      border: 'none',
                      background: '#dc2626',
                      color: 'white',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {rejectMutation.isPending ? 'Rejecting...' : 'Confirm Rejection'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
