import { Link } from 'react-router-dom'

import { useDeleteNotification, useMarkNotificationRead, useNotifications } from '../hooks/useNotifications'
import { NotificationList } from './NotificationList'

export function NotificationDropdown({ onClose }: { onClose: () => void }) {
  const { data, isLoading } = useNotifications({ limit: 5 })
  const markRead = useMarkNotificationRead()
  const remove = useDeleteNotification()

  return (
    <div className="notification-dropdown" role="dialog" aria-label="Notifications récentes">
      <div className="notification-dropdown-header"><strong>Notifications</strong><Link to="/notifications" onClick={onClose}>Voir tout</Link></div>
      {isLoading ? <div className="notification-dropdown-loading">Chargement...</div> : <NotificationList notifications={data?.items ?? []} compact onMarkRead={(id) => markRead.mutate({ id })} onDelete={(id) => remove.mutate(id)} />}
      <Link className="notification-dropdown-footer" to="/notifications" onClick={onClose}>Voir toutes les notifications</Link>
    </div>
  )
}