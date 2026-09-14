import { useState } from 'react'

import { NotificationFilters } from '../components/NotificationFilters'
import { NotificationList } from '../components/NotificationList'
import { useDeleteNotification, useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from '../hooks/useNotifications'
import type { NotificationFilters as Filters } from '../types/notification'

export function NotificationsPage() {
  const [filters, setFilters] = useState<Filters>({ limit: 50, page: 1 })
  const { data, isLoading, isError, refetch } = useNotifications(filters)
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()
  const remove = useDeleteNotification()

  return (
    <main className="notifications-page page-shell">
      <header className="notifications-page-header">
        <div><p className="eyebrow">Activity center</p><h1>Notifications</h1><p className="page-subtitle">Les événements importants de votre espace de travail.</p></div>
        <button type="button" className="notifications-mark-all" onClick={() => markAllRead.mutate()} disabled={markAllRead.isPending || data?.unread_count === 0}>Tout marquer comme lu</button>
      </header>
      <NotificationFilters filters={filters} onChange={setFilters} />
      {isError && <div className="notification-error">Impossible de charger les notifications. <button type="button" onClick={() => refetch()}>Réessayer</button></div>}
      {isLoading ? <div className="notification-loading">Chargement des notifications...</div> : <NotificationList notifications={data?.items ?? []} onMarkRead={(id) => markRead.mutate({ id })} onDelete={(id) => remove.mutate(id)} />}
    </main>
  )
}