import type { InboxMessage } from '../types/inbox'
import { SentimentBadge } from './SentimentBadge'

interface InboxItemProps {
  message: InboxMessage
  isSelected: boolean
  onSelect: (message: InboxMessage) => void
}

export function InboxItem({ message, isSelected, onSelect }: InboxItemProps) {
  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMins / 60)
      const diffDays = Math.floor(diffHours / 24)

      if (diffMins < 1) return "À l'instant"
      if (diffMins < 60) return `Il y a ${diffMins} min`
      if (diffHours < 24) return `Il y a ${diffHours}h`
      if (diffDays < 7) return `Il y a ${diffDays}j`
      return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'COMMENT':
        return '💬'
      case 'MESSAGE':
        return '✉️'
      case 'MENTION':
        return '🔔'
      default:
        return '📝'
    }
  }

  const platform = message.social_account?.platform || message.social_account?.provider || 'social'
  const isMeta = platform.toLowerCase().includes('meta') || platform.toLowerCase().includes('facebook') || platform.toLowerCase().includes('instagram')

  return (
    <div
      className={`inbox-item-card ${isSelected ? 'selected' : ''} ${!message.is_read ? 'unread' : ''}`}
      onClick={() => onSelect(message)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onSelect(message)
        }
      }}
    >
      <div className="inbox-item-header">
        <div className="inbox-item-sender-row">
          {!message.is_read && <span className="unread-dot" title="Non lu" />}
          <span className="inbox-sender-name">{message.sender_name}</span>
          <span className="inbox-type-icon" title={message.type}>
            {getTypeIcon(message.type)}
          </span>
        </div>
        <span className="inbox-time">{formatTime(message.created_at)}</span>
      </div>

      <div className="inbox-item-meta-row">
        <span className={`platform-tag ${isMeta ? 'platform-meta' : 'platform-linkedin'}`}>
          {platform.toUpperCase()}
        </span>
        <SentimentBadge sentiment={message.sentiment} score={message.sentiment_score} />
        {message.is_resolved && (
          <span className="status-tag status-resolved">Traité</span>
        )}
      </div>

      <p className="inbox-item-snippet">
        {message.content.length > 120 ? `${message.content.substring(0, 120)}...` : message.content}
      </p>
    </div>
  )
}
