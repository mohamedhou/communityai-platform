import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../auth/hooks/useAuth'
import { getSocialAccounts } from '../../social-accounts/services/socialApi'
import { useEditorialCalendar } from '../hooks/useEditorialCalendar'
import { CalendarHeader } from '../components/CalendarHeader'
import { CalendarFilters } from '../components/CalendarFilters'
import { CalendarGrid } from '../components/CalendarGrid'

export function EditorialCalendarPage() {
  const { accessToken } = useAuth()

  // Fetch social accounts for account metadata and network badges
  const { data: socialAccounts = [] } = useQuery({
    queryKey: ['social-accounts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getSocialAccounts(accessToken)
    },
    enabled: !!accessToken,
  })

  const {
    viewMode,
    setViewMode,
    statusFilter,
    setStatusFilter,
    filterCounts,
    headerTitle,
    monthCells,
    weekCells,
    isLoading,
    isError,
    error,
    errorMessage,
    successMessage,
    navigatePrev,
    navigateNext,
    goToToday,
    handleDropPost,
    isMoving,
  } = useEditorialCalendar()

  if (isLoading) {
    return (
      <main className="page-shell">
        <div className="calendar-loading-container">
          <div className="calendar-spinner" />
          <p>Loading editorial calendar...</p>
        </div>
      </main>
    )
  }

  if (isError) {
    return (
      <main className="page-shell">
        <div className="calendar-error-container">
          <h2>Error loading calendar</h2>
          <p>{(error as Error)?.message || 'An unexpected error occurred.'}</p>
        </div>
      </main>
    )
  }

  return (
    <main className="page-shell">
      <div className="calendar-page-container">
        {/* Alerts & Notifications */}
        {errorMessage && (
          <div className="calendar-alert-banner alert-error" role="alert">
            <span>⚠️ {errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div className="calendar-alert-banner alert-success" role="status">
            <span>✓ {successMessage}</span>
          </div>
        )}

        {isMoving && (
          <div className="calendar-moving-indicator">
            <span>Updating publication schedule...</span>
          </div>
        )}

        {/* Main Header with Month/Week navigation & + New Post */}
        <CalendarHeader
          title={headerTitle}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onPrev={navigatePrev}
          onNext={navigateNext}
          onToday={goToToday}
        />

        {/* Filter Bar */}
        <CalendarFilters
          currentFilter={statusFilter}
          onFilterChange={setStatusFilter}
          filterCounts={filterCounts}
        />

        {/* Calendar Grid (Month / Week) */}
        <CalendarGrid
          viewMode={viewMode}
          monthCells={monthCells}
          weekCells={weekCells}
          socialAccounts={socialAccounts}
          onDropPost={handleDropPost}
        />
      </div>
    </main>
  )
}
