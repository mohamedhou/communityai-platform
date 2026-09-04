import type { InboxMessage } from '../types/inbox'
import { ReplyBox } from './ReplyBox'
import { SentimentBadge } from './SentimentBadge'

interface InboxDetailProps {
  message: InboxMessage | null
  onToggleRead: (messageId: number, currentRead: boolean) => Promise<any>
  onToggleResolved: (messageId: number, currentResolved: boolean) => Promise<any>
  onSuggestReply: (tone: string, instructions?: string) => Promise<string | undefined>
  onSendReply: (content: string) => Promise<any>
  isSuggesting: boolean
  isSending: boolean
}

export function InboxDetail({
  message,
  onToggleRead,
  onToggleResolved,
  onSuggestReply,
  onSendReply,
  isSuggesting,
  isSending,
}: InboxDetailProps) {
  if (!message) {
    return (
      <div className="inbox-detail-empty">
        <div className="inbox-detail-empty-icon">👈</div>
        <h3>Sélectionnez une interaction</h3>
        <p>Cliquez sur un message ou commentaire dans la liste de gauche pour l'analyser et y répondre.</p>
      </div>
    )
  }

  const formatFullDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('fr-FR', {
        dateStyle: 'full',
        timeStyle: 'short',
      })
    } catch {
      return dateStr
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'COMMENT':
        return 'Commentaire'
      case 'MESSAGE':
        return 'Message privé'
      case 'MENTION':
        return 'Mention publique'
      default:
        return type
    }
  }

  const platform = message.social_account?.platform || message.social_account?.provider || 'social'
  const accountName = message.social_account?.account_name || 'Compte Social'

  return (
    <div className="inbox-detail-container">
      {/* Top action header */}
      <div className="inbox-detail-header">
        <div className="inbox-detail-sender-info">
          <div className="inbox-detail-avatar">
            {message.sender_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="inbox-detail-sender-name">{message.sender_name}</h3>
            <p className="inbox-detail-account-sub">
              Via <span className="platform-highlight">{platform.toUpperCase()}</span> ({accountName})
              • <span className="type-highlight">{getTypeLabel(message.type)}</span>
            </p>
          </div>
        </div>

        <div className="inbox-detail-quick-actions">
          <button
            type="button"
            className={`btn-action ${message.is_read ? 'btn-action-active' : ''}`}
            onClick={() => onToggleRead(message.id, message.is_read)}
            title={message.is_read ? 'Marquer comme non lu' : 'Marquer comme lu'}
          >
            {message.is_read ? '📖 Lu' : '📬 Marquer lu'}
          </button>

          <button
            type="button"
            className={`btn-action ${message.is_resolved ? 'btn-action-resolved' : ''}`}
            onClick={() => onToggleResolved(message.id, message.is_resolved)}
            title={message.is_resolved ? 'Rouvrir l’interaction' : 'Marquer comme traité'}
          >
            {message.is_resolved ? '✅ Traité' : '⏳ Marquer traité'}
          </button>
        </div>
      </div>

      {/* Meta details strip */}
      <div className="inbox-detail-meta-bar">
        <div className="meta-bar-item">
          <span className="meta-bar-label">Sentiment :</span>
          <SentimentBadge
            sentiment={message.sentiment}
            score={message.sentiment_score}
            showScore={true}
          />
        </div>

        <div className="meta-bar-item">
          <span className="meta-bar-label">Reçu le :</span>
          <span className="meta-bar-value">{formatFullDate(message.created_at)}</span>
        </div>

        {message.replied_at && (
          <div className="meta-bar-item replied-status">
            <span className="meta-bar-label">Répondu le :</span>
            <span className="meta-bar-value">{formatFullDate(message.replied_at)}</span>
          </div>
        )}
      </div>

      {/* Message Content Bubble */}
      <div className="inbox-detail-message-card">
        <div className="message-card-header">
          <span className="message-type-badge">{getTypeLabel(message.type)}</span>
          <span className="message-origin-id">ID Externe: {message.external_id}</span>
        </div>
        <div className="message-card-body">
          <p>{message.content}</p>
        </div>
      </div>

      {/* Reply Box */}
      <ReplyBox
        onSuggestReply={onSuggestReply}
        onSendReply={onSendReply}
        isSuggesting={isSuggesting}
        isSending={isSending}
        isResolved={message.is_resolved}
      />
    </div>
  )
}
