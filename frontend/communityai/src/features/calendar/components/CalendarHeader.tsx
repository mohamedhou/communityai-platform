import { Link } from 'react-router-dom'
import type { CalendarViewMode } from '../types/calendar'

interface CalendarHeaderProps {
  title: string
  viewMode: CalendarViewMode
  onViewModeChange: (mode: CalendarViewMode) => void
  onPrev: () => void
  onNext: () => void
  onToday: () => void
}

export function CalendarHeader({
  title,
  viewMode,
  onViewModeChange,
  onPrev,
  onNext,
  onToday,
}: CalendarHeaderProps) {
  return (
    <div className="calendar-header-panel">
      <div className="calendar-nav-group">
        <div className="calendar-nav-buttons">
          <button
            type="button"
            onClick={onPrev}
            aria-label="Previous period"
            className="calendar-nav-btn"
            title="Previous"
          >
            ‹
          </button>
          <button
            type="button"
            onClick={onToday}
            className="calendar-today-btn"
            title="Go to Today"
          >
            Today
          </button>
          <button
            type="button"
            onClick={onNext}
            aria-label="Next period"
            className="calendar-nav-btn"
            title="Next"
          >
            ›
          </button>
        </div>

        <h2 className="calendar-period-title">{title}</h2>
      </div>

      <div className="calendar-actions-group">
        <div className="calendar-view-toggle">
          <button
            type="button"
            onClick={() => onViewModeChange('month')}
            className={`calendar-toggle-btn ${viewMode === 'month' ? 'active' : ''}`}
          >
            Month
          </button>
          <button
            type="button"
            onClick={() => onViewModeChange('week')}
            className={`calendar-toggle-btn ${viewMode === 'week' ? 'active' : ''}`}
          >
            Week
          </button>
        </div>

        <Link
          to="/posts/new"
          className="calendar-new-post-btn"
        >
          <span style={{ fontSize: '1.2rem', lineHeight: 1, marginRight: '4px' }}>+</span> New Post
        </Link>
      </div>
    </div>
  )
}
