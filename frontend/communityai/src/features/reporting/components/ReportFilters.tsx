import type { SocialAccount } from '../../social-accounts/types/social'
import type { ReportFilters } from '../types/reporting'

interface ReportFiltersProps {
  filters: ReportFilters
  accounts: SocialAccount[]
  onChange: (filters: ReportFilters) => void
  onPreview: () => void
  isLoading: boolean
}

export function ReportFilters({ filters, accounts, onChange, onPreview, isLoading }: ReportFiltersProps) {
  const visibleAccounts = filters.platform ? accounts.filter((account) => account.platform.toLowerCase() === filters.platform || account.provider.toLowerCase() === filters.platform) : accounts
  return <div className="report-filters analytics-filters-bar">
    <div className="report-filter-grid">
      <label>Platform<select value={filters.platform ?? ''} onChange={(event) => onChange({ ...filters, platform: event.target.value || undefined, social_account_id: undefined })}><option value="">All platforms</option><option value="meta">Meta</option><option value="facebook">Facebook</option><option value="instagram">Instagram</option><option value="linkedin">LinkedIn</option></select></label>
      <label>Social account<select value={filters.social_account_id ?? ''} onChange={(event) => onChange({ ...filters, social_account_id: event.target.value ? Number(event.target.value) : undefined })}><option value="">All accounts</option>{visibleAccounts.map((account) => <option key={account.id} value={account.id}>{account.account_name}</option>)}</select></label>
      <label>Start date<input type="date" value={filters.start_date} max={filters.end_date} onChange={(event) => onChange({ ...filters, start_date: event.target.value })} /></label>
      <label>End date<input type="date" value={filters.end_date} min={filters.start_date} onChange={(event) => onChange({ ...filters, end_date: event.target.value })} /></label>
    </div>
    <button type="button" className="btn btn-primary report-preview-button" onClick={onPreview} disabled={isLoading || !filters.start_date || !filters.end_date}>{isLoading ? 'Génération...' : 'Aperçu'}</button>
  </div>
}