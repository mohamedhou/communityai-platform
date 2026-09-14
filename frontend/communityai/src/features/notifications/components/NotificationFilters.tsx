import type { NotificationFilters as Filters } from '../types/notification'

interface NotificationFiltersProps {
  filters: Filters
  onChange: (filters: Filters) => void
}

export function NotificationFilters({ filters, onChange }: NotificationFiltersProps) {
  const setRead = (is_read?: boolean) => onChange({ ...filters, is_read, page: 1 })
  return (
    <div className="notification-filters" role="tablist" aria-label="Filtres des notifications">
      <button type="button" className={filters.is_read === undefined ? 'active' : ''} onClick={() => setRead()}>Toutes</button>
      <button type="button" className={filters.is_read === false ? 'active' : ''} onClick={() => setRead(false)}>Non lues</button>
      <button type="button" className={filters.severity === 'SUCCESS' ? 'active' : ''} onClick={() => onChange({ ...filters, severity: filters.severity === 'SUCCESS' ? undefined : 'SUCCESS', page: 1 })}>Succès</button>
      <button type="button" className={filters.severity === 'WARNING' ? 'active' : ''} onClick={() => onChange({ ...filters, severity: filters.severity === 'WARNING' ? undefined : 'WARNING', page: 1 })}>Alertes</button>
      <button type="button" className={filters.severity === 'ERROR' ? 'active' : ''} onClick={() => onChange({ ...filters, severity: filters.severity === 'ERROR' ? undefined : 'ERROR', page: 1 })}>Erreurs</button>
    </div>
  )
}