import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '../../auth/hooks/useAuth'
import * as postApi from '../services/postApi'
import { getSocialAccounts } from '../../social-accounts/services/socialApi'
import type { MediaAsset } from '../../media/types/media'
import { MediaPicker } from '../../media/components/MediaPicker'

export function CreatePostPage() {
  const { accessToken, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { postId } = useParams<{ postId?: string }>()
  const isEditMode = !!postId
  const isCommunityManager = user?.role === 'COMMUNITY_MANAGER'

  const locationContent = (location.state as { content?: string } | null)?.content || ''
  const [content, setContent] = useState(locationContent)
  const [mediaUrl, setMediaUrl] = useState('')
  const [mediaAsset, setMediaAsset] = useState<MediaAsset | null>(null)
  const [socialAccountId, setSocialAccountId] = useState<number | ''>('')
  const [isScheduling, setIsScheduling] = useState(false)
  const [scheduledAt, setScheduledAt] = useState('')

  // Fetch social accounts
  const { data: accounts, isLoading: accountsLoading } = useQuery({
    queryKey: ['social-accounts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getSocialAccounts(accessToken)
    },
    enabled: !!accessToken,
  })

  // Fetch post details if editing
  const { data: existingPost, isLoading: postLoading } = useQuery({
    queryKey: ['post', postId],
    queryFn: () => {
      if (!accessToken || !postId) throw new Error('Not authenticated')
      return postApi.getPost(accessToken, parseInt(postId, 10))
    },
    enabled: !!accessToken && isEditMode,
  })
  const canSchedule = !isCommunityManager || existingPost?.approval_status === 'APPROVED'

  useEffect(() => {
    if (existingPost) {
      setContent(existingPost.content)
      setMediaUrl(existingPost.media_url || '')
      setMediaAsset(null)
      setSocialAccountId(existingPost.social_account_id)
      if (existingPost.scheduled_at) {
        setIsScheduling(true)
        // Convert to datetime-local format: YYYY-MM-DDTHH:MM
        const dateObj = new Date(existingPost.scheduled_at)
        const pad = (n: number) => n.toString().padStart(2, '0')
        const formatted = `${dateObj.getFullYear()}-${pad(dateObj.getMonth() + 1)}-${pad(dateObj.getDate())}T${pad(dateObj.getHours())}:${pad(dateObj.getMinutes())}`
        setScheduledAt(formatted)
      }
    }
  }, [existingPost])

  // Submit for Review mutation
  const submitReviewMutation = useMutation({
    mutationFn: (id: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.submitForReview(accessToken, id)
    },
    onSuccess: () => {
      alert('Post submitted for review!')
      navigate('/posts')
    },
    onError: (err: any) => {
      alert(`Submit for review failed: ${err.message}`)
      navigate('/posts')
    },
  })

  // Save as Draft mutation
  const saveMutation = useMutation({
    mutationFn: (params: {
      payload: { content: string; social_account_id: number; media_url?: string; media_asset_id?: number | null }
      andSubmit?: boolean
    }) => {
      if (!accessToken) throw new Error('Not authenticated')
      if (isEditMode && postId) {
        return postApi.updatePost(accessToken, parseInt(postId, 10), params.payload)
      }
      return postApi.createPost(accessToken, params.payload)
    },
    onSuccess: (post, variables) => {
      if (variables.andSubmit) {
        submitReviewMutation.mutate(post.id)
      } else if (isScheduling && scheduledAt) {
        // Schedule after saving
        scheduleMutation.mutate({ postId: post.id, scheduledAt })
      } else {
        navigate('/posts')
      }
    },
    onError: (err: any) => {
      alert(`Save failed: ${err.message}`)
    },
  })

  // Schedule mutation
  const scheduleMutation = useMutation({
    mutationFn: (params: { postId: number; scheduledAt: string }) => {
      if (!accessToken) throw new Error('Not authenticated')
      // Convert local date time to ISO string
      const isoStr = new Date(params.scheduledAt).toISOString()
      return postApi.schedulePost(accessToken, params.postId, isoStr)
    },
    onSuccess: () => {
      navigate('/posts')
    },
    onError: (err: any) => {
      alert(`Scheduling failed: ${err.message}`)
    },
  })

  // Publish immediate mutation
  const publishMutation = useMutation({
    mutationFn: (payload: { content: string; social_account_id: number; media_url?: string }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.createPost(accessToken, payload)
    },
    onSuccess: (post) => {
      // Publish immediately after creation
      triggerPublishMutation.mutate(post.id)
    },
    onError: (err: any) => {
      alert(`Publishing failed: ${err.message}`)
    },
  })

  const triggerPublishMutation = useMutation({
    mutationFn: (id: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return postApi.publishPost(accessToken, id)
    },
    onSuccess: () => {
      navigate('/posts')
    },
    onError: (err: any) => {
      alert(`Publishing failed: ${err.message}`)
      navigate('/posts')
    },
  })

  const handleSubmit = (e: React.FormEvent, action: 'save' | 'save_and_submit' | 'publish') => {
    e.preventDefault()
    if (!socialAccountId) {
      alert('Please select a social account')
      return
    }
    if (!content.trim()) {
      alert('Content cannot be empty')
      return
    }

    const payload = {
      content,
      social_account_id: Number(socialAccountId),
      media_url: mediaUrl || undefined,
      media_asset_id: mediaAsset?.id ?? null,
    }

    if (action === 'publish') {
      publishMutation.mutate(payload)
    } else if (action === 'save_and_submit') {
      saveMutation.mutate({ payload, andSubmit: true })
    } else {
      saveMutation.mutate({ payload, andSubmit: false })
    }
  }

  const selectedAccount = accounts?.find((a) => a.id === socialAccountId)

  if (accountsLoading || (isEditMode && postLoading)) {
    return <div className="social-loading">Loading form...</div>
  }

  return (
    <main className="page-shell">
      <div className="social-container" style={{ maxWidth: '900px' }}>
        <h1>{isEditMode ? 'Edit Publication' : 'New Publication'}</h1>
        <p className="page-subtitle">Compose your message and preview how it will look.</p>

        {/* Approval Status Alerts */}
        {isEditMode && existingPost?.approval_status === 'REJECTED' && existingPost.rejection_reason && (
          <div
            style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '16px',
              borderRadius: '8px',
              marginTop: '16px',
            }}
          >
            <h4 style={{ margin: '0 0 6px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
              ✕ Changes Requested by Reviewer
            </h4>
            <p style={{ margin: 0, fontSize: '0.95rem' }}>{existingPost.rejection_reason}</p>
            <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: '#7f1d1d' }}>
              Please update your post content accordingly, then click <strong>Save & Submit for Review</strong>.
            </p>
          </div>
        )}

        {isEditMode && existingPost?.approval_status === 'PENDING' && (
          <div
            style={{
              background: '#fffbeb',
              border: '1px solid #fef3c7',
              color: '#92400e',
              padding: '14px',
              borderRadius: '8px',
              marginTop: '16px',
              fontSize: '0.9rem',
            }}
          >
            ⏳ <strong>Pending Review:</strong> This publication is currently awaiting reviewer approval. Modifying it will update the pending draft.
          </div>
        )}

        {isEditMode && existingPost?.approval_status === 'APPROVED' && (
          <div
            style={{
              background: '#fefce8',
              border: '1px solid #fef08a',
              color: '#854d0e',
              padding: '14px',
              borderRadius: '8px',
              marginTop: '16px',
              fontSize: '0.9rem',
            }}
          >
            ⚠️ <strong>Notice:</strong> This post has already been approved. Making changes will reset approval and require resubmission.
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', marginTop: '24px' }}>
          {/* Form */}
          <form style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label htmlFor="social-account-select" style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>
                Select Social Account
              </label>
              <select
                id="social-account-select"
                value={socialAccountId}
                onChange={(e) => setSocialAccountId(e.target.value ? Number(e.target.value) : '')}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #d1d5db' }}
              >
                <option value="">-- Choose Account --</option>
                {accounts?.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.account_name} ({acc.platform})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="post-content" style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>
                Content
              </label>
              <textarea
                id="post-content"
                rows={6}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="What do you want to share today?"
                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #d1d5db', resize: 'vertical' }}
              />
            </div>

            <div>
              <label htmlFor="media-url-input" style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>
                Media Image URL (Optional)
              </label>
              <input
                id="media-url-input"
                type="text"
                value={mediaUrl}
                onChange={(e) => setMediaUrl(e.target.value)}
                placeholder="https://example.com/image.png"
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #d1d5db' }}
              />
            </div>

            <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <strong>Workspace media</strong>
              <MediaPicker value={mediaAsset} onChange={setMediaAsset} />
            </div>

            {/* Schedule Section */}
            <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                <input
                  type="checkbox"
                  checked={isScheduling}
                  onChange={(e) => setIsScheduling(e.target.checked)}
                  disabled={!canSchedule}
                />
                Schedule for Later
              </label>
              {isCommunityManager && !canSchedule && (
                <p style={{ margin: '8px 0 0', color: '#92400e', fontSize: '0.85rem' }}>
                  Approval required before scheduling or publishing.
                </p>
              )}

              {isScheduling && (
                <div style={{ marginTop: '10px' }}>
                  <label htmlFor="scheduled-time" style={{ display: 'block', fontSize: '0.9rem', marginBottom: '4px' }}>
                    Scheduled Time
                  </label>
                  <input
                    id="scheduled-time"
                    type="datetime-local"
                    value={scheduledAt}
                    onChange={(e) => setScheduledAt(e.target.value)}
                    style={{ padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                  />
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={(e) => handleSubmit(e, 'save')}
                disabled={saveMutation.isPending || submitReviewMutation.isPending}
                className="action-btn btn-refresh"
                style={{ flex: 1, minWidth: '120px', padding: '12px' }}
              >
                {saveMutation.isPending ? 'Saving...' : isEditMode ? 'Save Draft' : 'Save as Draft'}
              </button>

              <button
                type="button"
                onClick={(e) => handleSubmit(e, 'save_and_submit')}
                disabled={saveMutation.isPending || submitReviewMutation.isPending}
                className="action-btn"
                style={{
                  flex: 1,
                  minWidth: '160px',
                  padding: '12px',
                  background: '#fef3c7',
                  color: '#92400e',
                  border: '1px solid #fde68a',
                  fontWeight: 600,
                }}
              >
                {submitReviewMutation.isPending ? 'Submitting...' : 'Save & Submit for Review'}
              </button>
              
              {!isEditMode && (
                <button
                  type="button"
                  onClick={(e) => handleSubmit(e, 'publish')}
                  disabled={publishMutation.isPending || triggerPublishMutation.isPending || !canSchedule}
                  className="connect-btn btn-linkedin"
                  style={{ flex: 1, minWidth: '140px', padding: '12px', margin: 0 }}
                >
                  {publishMutation.isPending || triggerPublishMutation.isPending ? 'Publishing...' : 'Publish Immediately'}
                </button>
              )}
            </div>
          </form>

          {/* Preview */}
          <div style={{ border: '1px solid #e5e7eb', borderRadius: '12px', padding: '24px', background: '#f3f4f6' }}>
            <h3>Preview</h3>
            <div style={{ background: '#ffffff', borderRadius: '12px', padding: '16px', marginTop: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#d1d5db', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
                  {selectedAccount ? selectedAccount.account_name.charAt(0) : 'U'}
                </div>
                <div>
                  <h4 style={{ margin: 0 }}>{selectedAccount ? selectedAccount.account_name : 'Social Page Name'}</h4>
                  <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                    {selectedAccount ? `@${selectedAccount.platform}` : 'Select a network'}
                  </span>
                </div>
              </div>

              <div style={{ fontSize: '0.95rem', color: '#1f2937', marginBottom: '12px', minHeight: '60px', whiteSpace: 'pre-wrap' }}>
                {content || 'Your publication content will appear here...'}
              </div>

              {mediaUrl && (
                <div style={{ maxHeight: '200px', overflow: 'hidden', borderRadius: '8px', border: '1px solid #e5e7eb', background: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <img src={mediaUrl} alt="Preview media" style={{ maxWidth: '100%', maxHeight: '200px' }} onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none'
                  }} />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#9ca3af', marginTop: '16px', borderTop: '1px solid #f3f4f6', paddingTop: '8px' }}>
                <span>Character Count: {content.length}</span>
                {selectedAccount && <span>Platform: {selectedAccount.platform.toUpperCase()}</span>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
