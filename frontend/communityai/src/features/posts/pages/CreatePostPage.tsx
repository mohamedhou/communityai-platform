import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '../../auth/hooks/useAuth'
import * as postApi from '../services/postApi'
import { getSocialAccounts } from '../../social-accounts/services/socialApi'

export function CreatePostPage() {
  const { accessToken } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { postId } = useParams<{ postId?: string }>()
  const isEditMode = !!postId

  const locationContent = (location.state as { content?: string } | null)?.content || ''
  const [content, setContent] = useState(locationContent)
  const [mediaUrl, setMediaUrl] = useState('')
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

  useEffect(() => {
    if (existingPost) {
      setContent(existingPost.content)
      setMediaUrl(existingPost.media_url || '')
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

  // Save as Draft mutation
  const saveMutation = useMutation({
    mutationFn: (payload: { content: string; social_account_id: number; media_url?: string }) => {
      if (!accessToken) throw new Error('Not authenticated')
      if (isEditMode && postId) {
        return postApi.updatePost(accessToken, parseInt(postId, 10), payload)
      }
      return postApi.createPost(accessToken, payload)
    },
    onSuccess: (post) => {
      if (isScheduling && scheduledAt) {
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

  const handleSubmit = (e: React.FormEvent, action: 'save' | 'publish') => {
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
    }

    if (action === 'publish') {
      publishMutation.mutate(payload)
    } else {
      saveMutation.mutate(payload)
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

            {/* Schedule Section */}
            <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                <input
                  type="checkbox"
                  checked={isScheduling}
                  onChange={(e) => setIsScheduling(e.target.checked)}
                />
                Schedule for Later
              </label>

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

            <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
              <button
                type="button"
                onClick={(e) => handleSubmit(e, 'save')}
                disabled={saveMutation.isPending}
                className="action-btn btn-refresh"
                style={{ flex: 1, padding: '12px' }}
              >
                {saveMutation.isPending ? 'Saving...' : isEditMode ? 'Update Draft' : 'Save as Draft'}
              </button>
              
              {!isEditMode && (
                <button
                  type="button"
                  onClick={(e) => handleSubmit(e, 'publish')}
                  disabled={publishMutation.isPending || triggerPublishMutation.isPending}
                  className="connect-btn btn-linkedin"
                  style={{ flex: 1, padding: '12px', margin: 0 }}
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
