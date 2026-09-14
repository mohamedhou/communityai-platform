import { useNavigate } from 'react-router-dom'

import type { Notification } from '../types/notification'

const icons: Record<Notification['type'], string> = {
  POST_PUBLISHED: '✓',
  POST_FAILED: '!',
  POST_SCHEDULED: '◷',
  INBOX_MESSAGE: '◌',
  AI_SUGGESTION: '✦',
  SOCIAL_ACCOUNT: '◎',
  ANALYTICS: '↗',
  SYSTEM: 'i',
}

const relativeDate = (value: string) => {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000))
  if (seconds < 60) return "À l'instant"
  if (seconds < 3600) return `Il y a ${Math.floor(seconds / 60)} min`
  if (seconds < 86400) return `Il y a ${Math.floor(seconds / 3600)} h`
  return `Il y a ${Math.floor(seconds / 86400)} j`
}

interface NotificationItemProps {
  notification: Notification
  compact?: boolean
  onMarkRead: (id: number) => void
  onDelete: (id: number) => void
}

export function NotificationItem({ notification, compact = false, onMarkRead, onDelete }: NotificationItemProps) {
  const navigate = useNavigate()
  const openNotification = () => {
    if (!notification.is_read) onMarkRead(notification.id)
    if (notification.action_url) navigate(notification.action_url)
  }

  return (
    <article className={`notification-item ${notification.is_read ? 'is-read' : 'is-unread'} ${compact ? 'is-compact' : ''}`}>
      <button type="button" className={`notification-icon severity-${notification.severity.toLowerCase()}`} onClick={openNotification} aria-label={`Ouvrir : ${notification.title}`}>
        {icons[notification.type]}
      </button>
      <button type="button" className="notification-content" onClick={openNotification}>
        <span className="notification-item-heading"><strong>{notification.title}</strong><time>{relativeDate(notification.created_at)}</time></span>
        <span className="notification-message">{notification.message}</span>
        {!compact && <span className={`notification-severity severity-text-${notification.severity.toLowerCase()}`}>{notification.severity}</span>}
      </button>
      {!compact && (
        <span className="notification-actions">
          {!notification.is_read && <button type="button" title="Marquer comme lu" onClick={() => onMarkRead(notification.id)}>Lu</button>}
          <button type="button" title="Supprimer" onClick={() => onDelete(notification.id)}>Supprimer</button>
        </span>
      )}
    </article>
  )
}