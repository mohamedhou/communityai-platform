import type { CalendarFilterStatus } from '../types/calendar'

interface CalendarFiltersProps {
  currentFilter: CalendarFilterStatus
  onFilterChange: (filter: CalendarFilterStatus) => void
  filterCounts: Record<CalendarFilterStatus, number>
}

const FILTERS: { key: CalendarFilterStatus; label: string }[] = [
  { key: 'ALL', label: 'All' },
  { key: 'DRAFT', label: 'Draft' },
  { key: 'SCHEDULED', label: 'Scheduled' },
  { key: 'PUBLISHING', label: 'Publishing' },
  { key: 'PUBLISHED', label: 'Published' },
  { key: 'FAILED', label: 'Failed' },
  { key: 'CANCELLED', label: 'Cancelled' },
]

export function CalendarFilters({
  currentFilter,
  onFilterChange,
  filterCounts,
}: CalendarFiltersProps) {
  return (
    <div className="calendar-filters-bar">
      <span className="calendar-filters-label">Filters:</span>
      <div className="calendar-filters-list">
        {FILTERS.map(({ key, label }) => {
          const isActive = currentFilter === key
          const count = filterCounts[key] ?? 0

          return (
            <button
              key={key}
              type="button"
              onClick={() => onFilterChange(key)}
              className={`calendar-filter-pill ${key.toLowerCase()} ${isActive ? 'active' : ''}`}
            >
              <span>{label}</span>
              <span className="calendar-filter-count">{count}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
