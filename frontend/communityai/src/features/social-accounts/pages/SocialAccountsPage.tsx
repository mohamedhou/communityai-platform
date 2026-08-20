import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import { useAuth } from '../../auth/hooks/useAuth'
import * as socialApi from '../services/socialApi'

export function SocialAccountsPage() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const errorParam = searchParams.get('error')

  // Fetch social accounts
  const { data: accounts, isLoading, error } = useQuery({
    queryKey: ['social-accounts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return socialApi.getSocialAccounts(accessToken)
    },
    enabled: !!accessToken,
  })

  // Mutation to connect a platform (triggers redirect to provider)
  const connectMutation = useMutation({
    mutationFn: (platform: string) => {
      if (!accessToken) throw new Error('Not authenticated')
      return socialApi.getConnectUrl(accessToken, platform)
    },
    onSuccess: (data) => {
      // Redirect to provider OAuth or mock callback URL
      window.location.href = data.url
    },
  })

  // Mutation to disconnect account
  const disconnectMutation = useMutation({
    mutationFn: (accountId: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return socialApi.disconnectSocialAccount(accessToken, accountId)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['social-accounts'] })
    },
  })

  // Mutation to refresh token
  const refreshMutation = useMutation({
    mutationFn: (accountId: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return socialApi.refreshSocialAccountToken(accessToken, accountId)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['social-accounts'] })
      alert('Token refreshed successfully!')
    },
    onError: (err) => {
      alert(`Failed to refresh token: ${err.message}`)
    },
  })

  const handleConnect = (platform: string) => {
    connectMutation.mutate(platform)
  }

  const handleDisconnect = (accountId: number, name: string) => {
    if (confirm(`Are you sure you want to disconnect "${name}"?`)) {
      disconnectMutation.mutate(accountId)
    }
  }

  const handleRefresh = (accountId: number) => {
    refreshMutation.mutate(accountId)
  }

  const clearError = () => {
    setSearchParams({})
  }

  if (isLoading) {
    return <div className="social-loading">Loading social accounts...</div>
  }

  if (error) {
    return (
      <div className="social-error-page">
        Error loading social accounts: {(error as Error).message}
      </div>
    )
  }

  return (
    <main className="page-shell">
      <div className="social-container">
        <h1>Social Accounts</h1>
        <p className="page-subtitle">Connect and manage your social network profiles.</p>

        {errorParam && (
          <div className="error-banner">
            <span className="error-message">Connection failed: {decodeURIComponent(errorParam)}</span>
            <button type="button" onClick={clearError} className="error-dismiss">
              &times;
            </button>
          </div>
        )}

        {/* Integration Options */}
        <section className="integration-section">
          <h2>Available Integrations</h2>
          <div className="integration-grid">
            <div className="integration-card">
              <div className="integration-header">
                <span className="platform-icon meta-icon">M</span>
                <h3>Meta (Facebook & Instagram)</h3>
              </div>
              <p>Connect your Facebook Pages and Instagram Professional accounts via Meta.</p>
              <button
                type="button"
                onClick={() => handleConnect('meta')}
                disabled={connectMutation.isPending}
                className="connect-btn btn-meta"
              >
                {connectMutation.isPending ? 'Connecting...' : 'Connect Meta'}
              </button>
            </div>

            <div className="integration-card">
              <div className="integration-header">
                <span className="platform-icon linkedin-icon">in</span>
                <h3>LinkedIn</h3>
              </div>
              <p>Connect your personal LinkedIn profile or Company Page.</p>
              <button
                type="button"
                onClick={() => handleConnect('linkedin')}
                disabled={connectMutation.isPending}
                className="connect-btn btn-linkedin"
              >
                {connectMutation.isPending ? 'Connecting...' : 'Connect LinkedIn'}
              </button>
            </div>
          </div>
        </section>

        {/* Connected Channels List */}
        <section className="channels-section">
          <h2>Connected Channels</h2>
          {accounts && accounts.length > 0 ? (
            <div className="channels-list">
              {accounts.map((acc) => {
                const isLinkedIn = acc.provider === 'linkedin'
                
                return (
                  <div key={acc.id} className="channel-card">
                    <div className="channel-info">
                      <div className="avatar-wrapper">
                        {acc.profile_image_url ? (
                          <img
                            src={acc.profile_image_url}
                            alt={acc.account_name}
                            className="channel-avatar"
                          />
                        ) : (
                          <div className={`channel-avatar-fallback ${acc.platform}`}>
                            {acc.account_name.charAt(0)}
                          </div>
                        )}
                        <span className={`channel-platform-badge ${acc.platform}`}>
                          {acc.platform === 'facebook' ? 'f' : acc.platform === 'instagram' ? 'ig' : 'in'}
                        </span>
                      </div>

                      <div className="channel-details">
                        <h4>{acc.account_name}</h4>
                        {acc.account_username && (
                          <span className="channel-username">@{acc.account_username}</span>
                        )}
                        <div className="status-row">
                          <span className={`status-dot ${acc.status.toLowerCase()}`} />
                          <span className="status-label">{acc.status}</span>
                          {acc.token_expires_at && (
                            <span className="expiry-label">
                              &middot; Expires: {new Date(acc.token_expires_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="channel-actions">
                      {isLinkedIn && acc.status !== 'REVOKED' && (
                        <button
                          type="button"
                          onClick={() => handleRefresh(acc.id)}
                          disabled={refreshMutation.isPending}
                          className="action-btn btn-refresh"
                        >
                          Reconnect
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => handleDisconnect(acc.id, acc.account_name)}
                        disabled={disconnectMutation.isPending}
                        className="action-btn btn-disconnect"
                      >
                        Disconnect
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="empty-channels">
              <p>No social channels connected yet. Click on one of the integrations above to link your accounts.</p>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}
