import { useState } from 'react'

import { useUnreadNotificationCount } from '../hooks/useNotifications'
import { NotificationDropdown } from './NotificationDropdown'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const { data } = useUnreadNotificationCount()
  const unreadCount = data?.unread_count ?? 0

  return (
    <div className="notification-bell-wrapper">
      <button type="button" className="notification-bell" onClick={() => setOpen((value) => !value)} aria-expanded={open} aria-label={`Notifications${unreadCount ? `, ${unreadCount} non lues` : ''}`}>
        <span aria-hidden="true">♧</span>
        {unreadCount > 0 && <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>}
      </button>
      {open && <NotificationDropdown onClose={() => setOpen(false)} />}
    </div>
  )
}