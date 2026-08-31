import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/hooks/useAuth'
import * as postApi from '../services/postApi'
import { getSocialAccounts } from '../../social-accounts/services/socialApi'
import type { PostStatus } from '../types/post'

export function PostsPage() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<PostStatus | 'ALL'>('ALL')

  // Fetch posts
  const { data: posts, isLoading: postsLoading, error: postsError } = useQuery({
    queryKey: ['posts', statusFilter],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.getPosts(accessToken, statusFilter === 'ALL' ? undefined : statusFilter)
    },
    enabled: !!accessToken,
  })

  // Fetch social accounts (to map name/platform details)
  const { data: accounts } = useQuery({
    queryKey: ['social-accounts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getSocialAccounts(accessToken)
    },
    enabled: !!accessToken,
  })

  // Mutations
  const publishMutation = useMutation({
    mutationFn: (postId: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.publishPost(accessToken, postId)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['posts'] })
      alert('Post published successfully!')
    },
    onError: (err: any) => {
      alert(`Publishing failed: ${err.message}`)
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (postId: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.cancelPost(accessToken, postId)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (postId: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.deletePost(accessToken, postId)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
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

  if (postsLoading) {
    return <div className="social-loading">Loading publications...</div>
  }

  if (postsError) {
    return (
      <div className="social-error-page">
        Error loading posts: {(postsError as Error).message}
      </div>
    )
  }

  return (
    <main className="page-shell">
      <div className="social-container">
        <div className="posts-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h1>Publications</h1>
            <p className="page-subtitle">Draft, schedule, and publish posts to Meta & LinkedIn.</p>
          </div>
          <Link to="/posts/new" className="connect-btn btn-linkedin" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            New Publication
          </Link>
        </div>

        {/* Filters */}
        <div className="filters-row" style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
          {(['ALL', 'DRAFT', 'SCHEDULED', 'PUBLISHING', 'PUBLISHED', 'FAILED', 'CANCELLED'] as const).map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`action-btn ${statusFilter === st ? 'btn-refresh' : 'btn-disconnect'}`}
              style={{
                background: statusFilter === st ? '#2563eb' : '#f3f4f6',
                color: statusFilter === st ? '#ffffff' : '#374151',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Posts List */}
        {posts && posts.length > 0 ? (
          <div className="channels-list">
            {posts.map((post) => {
              const acc = getAccountInfo(post.social_account_id)
              const showPublish = post.status === 'DRAFT' || post.status === 'FAILED'
              const showCancel = post.status === 'SCHEDULED'
              const showDelete = post.status === 'DRAFT' || post.status === 'SCHEDULED' || post.status === 'FAILED' || post.status === 'CANCELLED'
              const showEdit = post.status === 'DRAFT' || post.status === 'SCHEDULED' || post.status === 'FAILED'

              return (
                <div key={post.id} className="channel-card" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '16px', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      {acc.avatar ? (
                        <img src={acc.avatar} alt={acc.name} className="channel-avatar" style={{ width: '40px', height: '40px' }} />
                      ) : (
                        <div className={`channel-avatar-fallback ${acc.platform}`} style={{ width: '40px', height: '40px' }}>
                          {acc.name.charAt(0)}
                        </div>
                      )}
                      <div>
                        <h4 style={{ margin: 0 }}>{acc.name}</h4>
                        <span className={`channel-platform-badge ${acc.platform}`} style={{ position: 'static', display: 'inline-block', marginTop: '4px' }}>
                          {acc.platform}
                        </span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`status-label status-dot ${post.status.toLowerCase()}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 'bold' }}>
                        {post.status}
                      </span>
                      {post.scheduled_at && (
                        <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>
                          Scheduled: {new Date(post.scheduled_at).toLocaleString()}
                        </div>
                      )}
                      {post.published_at && (
                        <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>
                          Published: {new Date(post.published_at).toLocaleString()}
                        </div>
                      )}
                    </div>
                  </div>

                  <div style={{ background: '#f9fafb', padding: '12px', borderRadius: '8px', border: '1px solid #e5e7eb', whiteSpace: 'pre-wrap' }}>
                    {post.content}
                  </div>

                  {post.media_url && (
                    <div style={{ fontSize: '0.85rem', color: '#2563eb' }}>
                      Media: <a href={post.media_url} target="_blank" rel="noreferrer">{post.media_url}</a>
                    </div>
                  )}

                  {post.error_message && (
                    <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '8px 12px', borderRadius: '6px', fontSize: '0.9rem' }}>
                      <strong>Error:</strong> {post.error_message}
                    </div>
                  )}

                  {post.external_post_id && (
                    <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                      External Post ID: <code>{post.external_post_id}</code>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', borderTop: '1px solid #f3f4f6', paddingTop: '12px' }}>
                    {showPublish && (
                      <button
                        type="button"
                        onClick={() => publishMutation.mutate(post.id)}
                        disabled={publishMutation.isPending}
                        className="action-btn btn-refresh"
                      >
                        Publish Now
                      </button>
                    )}
                    {showCancel && (
                      <button
                        type="button"
                        onClick={() => cancelMutation.mutate(post.id)}
                        disabled={cancelMutation.isPending}
                        className="action-btn btn-disconnect"
                        style={{ background: '#d97706', color: 'white' }}
                      >
                        Cancel
                      </button>
                    )}
                    {showEdit && (
                      <button
                        type="button"
                        onClick={() => navigate(`/posts/${post.id}/edit`)}
                        className="action-btn btn-disconnect"
                      >
                        Edit
                      </button>
                    )}
                    {showDelete && (
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm('Delete this draft?')) {
                            deleteMutation.mutate(post.id)
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="action-btn btn-disconnect"
                        style={{ color: '#dc2626' }}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="empty-channels">
            <p>No publications found matching this filter.</p>
          </div>
        )}
      </div>
    </main>
  )
}
