import type { Notification } from '../types/notification'
import { NotificationEmptyState } from './NotificationEmptyState'
import { NotificationItem } from './NotificationItem'

interface NotificationListProps {
  notifications: Notification[]
  compact?: boolean
  onMarkRead: (id: number) => void
  onDelete: (id: number) => void
}

export function NotificationList({ notifications, compact = false, onMarkRead, onDelete }: NotificationListProps) {
  if (notifications.length === 0) return <NotificationEmptyState />
  return (
    <div className="notification-list">
      {notifications.map((notification) => <NotificationItem key={notification.id} notification={notification} compact={compact} onMarkRead={onMarkRead} onDelete={onDelete} />)}
    </div>
  )
}