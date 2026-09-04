import type { InboxFiltersState, InboxMessageType, InboxSentiment } from '../types/inbox'

interface InboxFiltersProps {
  filters: InboxFiltersState
  onChange: (filters: InboxFiltersState) => void
  unreadCount?: number
}

export function InboxFilters({ filters, onChange, unreadCount = 0 }: InboxFiltersProps) {
  const handleTypeChange = (type: InboxMessageType | 'ALL') => {
    onChange({ ...filters, type })
  }

  const handlePlatformChange = (platform: string) => {
    onChange({ ...filters, platform })
  }

  const handleSentimentChange = (sentiment: InboxSentiment | 'ALL') => {
    onChange({ ...filters, sentiment })
  }

  const handleStatusChange = (status: 'ALL' | 'UNREAD' | 'READ' | 'RESOLVED') => {
    onChange({ ...filters, status })
  }

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, search: e.target.value })
  }

  const currentType = filters.type || 'ALL'
  const currentPlatform = filters.platform || 'ALL'
  const currentSentiment = filters.sentiment || 'ALL'
  const currentStatus = filters.status || 'ALL'

  return (
    <div className="inbox-filters-container">
      {/* Top Search bar */}
      <div className="inbox-search-bar">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          placeholder="Rechercher par expéditeur, contenu..."
          value={filters.search || ''}
          onChange={handleSearchChange}
          className="inbox-search-input"
        />
        {filters.search && (
          <button
            type="button"
            className="search-clear-btn"
            onClick={() => onChange({ ...filters, search: '' })}
          >
            ✕
          </button>
        )}
      </div>

      {/* Filter Groups */}
      <div className="inbox-filter-groups">
        {/* Type Filter */}
        <div className="filter-group">
          <span className="filter-label">Type :</span>
          <div className="filter-pills">
            <button
              type="button"
              className={`pill-btn ${currentType === 'ALL' ? 'active' : ''}`}
              onClick={() => handleTypeChange('ALL')}
            >
              Tous
            </button>
            <button
              type="button"
              className={`pill-btn ${currentType === 'COMMENT' ? 'active' : ''}`}
              onClick={() => handleTypeChange('COMMENT')}
            >
              💬 Commentaires
            </button>
            <button
              type="button"
              className={`pill-btn ${currentType === 'MESSAGE' ? 'active' : ''}`}
              onClick={() => handleTypeChange('MESSAGE')}
            >
              ✉️ Messages
            </button>
            <button
              type="button"
              className={`pill-btn ${currentType === 'MENTION' ? 'active' : ''}`}
              onClick={() => handleTypeChange('MENTION')}
            >
              🔔 Mentions
            </button>
          </div>
        </div>

        {/* Network / Platform Filter */}
        <div className="filter-group">
          <span className="filter-label">Réseau :</span>
          <div className="filter-pills">
            <button
              type="button"
              className={`pill-btn ${currentPlatform === 'ALL' ? 'active' : ''}`}
              onClick={() => handlePlatformChange('ALL')}
            >
              Tous
            </button>
            <button
              type="button"
              className={`pill-btn ${currentPlatform.toLowerCase() === 'meta' ? 'active' : ''}`}
              onClick={() => handlePlatformChange('meta')}
            >
              Meta
            </button>
            <button
              type="button"
              className={`pill-btn ${currentPlatform.toLowerCase() === 'linkedin' ? 'active' : ''}`}
              onClick={() => handlePlatformChange('linkedin')}
            >
              LinkedIn
            </button>
          </div>
        </div>

        {/* Sentiment Filter */}
        <div className="filter-group">
          <span className="filter-label">Sentiment :</span>
          <div className="filter-pills">
            <button
              type="button"
              className={`pill-btn ${currentSentiment === 'ALL' ? 'active' : ''}`}
              onClick={() => handleSentimentChange('ALL')}
            >
              Tous
            </button>
            <button
              type="button"
              className={`pill-btn pill-positive ${currentSentiment === 'POSITIVE' ? 'active' : ''}`}
              onClick={() => handleSentimentChange('POSITIVE')}
            >
              Positif
            </button>
            <button
              type="button"
              className={`pill-btn pill-neutral ${currentSentiment === 'NEUTRAL' ? 'active' : ''}`}
              onClick={() => handleSentimentChange('NEUTRAL')}
            >
              Neutre
            </button>
            <button
              type="button"
              className={`pill-btn pill-negative ${currentSentiment === 'NEGATIVE' ? 'active' : ''}`}
              onClick={() => handleSentimentChange('NEGATIVE')}
            >
              Négatif
            </button>
          </div>
        </div>

        {/* Status Filter */}
        <div className="filter-group">
          <span className="filter-label">Statut :</span>
          <div className="filter-pills">
            <button
              type="button"
              className={`pill-btn ${currentStatus === 'ALL' ? 'active' : ''}`}
              onClick={() => handleStatusChange('ALL')}
            >
              Tous
            </button>
            <button
              type="button"
              className={`pill-btn ${currentStatus === 'UNREAD' ? 'active' : ''}`}
              onClick={() => handleStatusChange('UNREAD')}
            >
              Non lus {unreadCount > 0 && <span className="pill-badge">{unreadCount}</span>}
            </button>
            <button
              type="button"
              className={`pill-btn ${currentStatus === 'READ' ? 'active' : ''}`}
              onClick={() => handleStatusChange('READ')}
            >
              Lus
            </button>
            <button
              type="button"
              className={`pill-btn ${currentStatus === 'RESOLVED' ? 'active' : ''}`}
              onClick={() => handleStatusChange('RESOLVED')}
            >
              Traités
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
