import { useState } from 'react'

import { InboxDetail } from '../components/InboxDetail'
import { InboxFilters } from '../components/InboxFilters'
import { InboxList } from '../components/InboxList'
import { useInbox } from '../hooks/useInbox'

export function InboxPage() {
  const {
    filters,
    setFilters,
    hasActiveFilters,
    resetFilters,
    messages,
    total,
    unreadCount,
    selectedMessage,
    selectMessage,
    isLoading,
    isError,
    error,
    refetchMessages,
    toggleRead,
    toggleResolved,
    suggestReply,
    sendReply,
    seedMock,
    isSuggesting,
    isSending,
    isSeeding,
  } = useInbox()

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleSeedMock = async () => {
    try {
      setNotification(null)
      await seedMock()
      setNotification({ type: 'success', message: 'Interactions de démonstration créées avec succès !' })
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Impossible de générer les données démo.' })
    }
  }

  const handleSuggest = async (tone: string, instructions?: string) => {
    if (!selectedMessage) return undefined
    return suggestReply(selectedMessage.id, tone, instructions)
  }

  const handleSend = async (content: string) => {
    if (!selectedMessage) return
    await sendReply(selectedMessage.id, content)
  }

  return (
    <div className="inbox-page-wrapper">
      {/* Page Header */}
      <div className="inbox-page-header">
        <div className="inbox-title-group">
          <div className="inbox-title-row">
            <h1 className="inbox-main-title">📥 Unified Inbox</h1>
            {unreadCount > 0 && (
              <span className="unread-counter-badge" title={`${unreadCount} messages non lus`}>
                {unreadCount} non lu{unreadCount > 1 ? 's' : ''}
              </span>
            )}
          </div>
          <p className="inbox-subtitle">
            Centralisez et traitez vos commentaires, messages privés et mentions Meta &amp; LinkedIn avec assistance IA.
          </p>
        </div>

        <div className="inbox-header-actions">
          <button
            type="button"
            className="btn btn-secondary btn-icon-only"
            onClick={() => refetchMessages()}
            title="Rafraîchir"
            disabled={isLoading}
          >
            🔄
          </button>

          <button
            type="button"
            className="btn btn-outline"
            onClick={handleSeedMock}
            disabled={isSeeding}
            title="Générer des exemples d'interactions (Mode Mock)"
          >
            {isSeeding ? 'Génération...' : '🧪 Données démo'}
          </button>
        </div>
      </div>

      {notification && (
        <div className={`inbox-banner-alert ${notification.type === 'success' ? 'banner-success' : 'banner-error'}`}>
          <span>{notification.message}</span>
          <button type="button" onClick={() => setNotification(null)} className="banner-close-btn">
            ✕
          </button>
        </div>
      )}

      {isError && (
        <div className="inbox-banner-alert banner-error">
          <span>Erreur lors du chargement : {(error as Error)?.message || 'Erreur réseau'}</span>
          <button type="button" onClick={() => refetchMessages()} className="btn btn-sm btn-secondary">
            Réessayer
          </button>
        </div>
      )}

      {/* Filters Toolbar */}
      <InboxFilters
        filters={filters}
        onChange={setFilters}
        unreadCount={unreadCount}
      />

      {/* Main Split Layout */}
      <div className="inbox-workspace-grid">
        {/* Left Column: Interaction List */}
        <section className="inbox-list-column">
          <InboxList
            messages={messages}
            total={total}
            selectedMessage={selectedMessage}
            onSelectMessage={selectMessage}
            isLoading={isLoading}
            hasFilters={hasActiveFilters}
            onResetFilters={resetFilters}
            onSeedMock={handleSeedMock}
            isSeeding={isSeeding}
          />
        </section>

        {/* Right Column: Detail & Reply Panel */}
        <section className="inbox-detail-column">
          <InboxDetail
            message={selectedMessage}
            onToggleRead={toggleRead}
            onToggleResolved={toggleResolved}
            onSuggestReply={handleSuggest}
            onSendReply={handleSend}
            isSuggesting={isSuggesting}
            isSending={isSending}
          />
        </section>
      </div>
    </div>
  )
}
