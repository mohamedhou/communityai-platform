import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getSocialAccounts } from '../../social-accounts/services/socialApi'
import { useAuth } from '../../auth/hooks/useAuth'
import { ReportEmptyState } from '../components/ReportEmptyState'
import { ReportExportButtons } from '../components/ReportExportButtons'
import { ReportFilters } from '../components/ReportFilters'
import { ReportPreview } from '../components/ReportPreview'
import { useReportExport, useReportPreview } from '../hooks/useReporting'
import type { ReportFilters as ReportFilterState } from '../types/reporting'

const initialFilters = (): ReportFilterState => {
  const end = new Date()
  const start = new Date(end)
  start.setDate(end.getDate() - 29)
  return { start_date: start.toISOString().slice(0, 10), end_date: end.toISOString().slice(0, 10) }
}

export function ReportingPage() {
  const { accessToken } = useAuth()
  const [filters, setFilters] = useState<ReportFilterState>(initialFilters)
  const [success, setSuccess] = useState('')
  const { data: accounts = [] } = useQuery({ queryKey: ['social-accounts'], queryFn: () => getSocialAccounts(accessToken!), enabled: Boolean(accessToken) })
  const previewQuery = useReportPreview(filters)
  const exportMutation = useReportExport()
  const preview = () => { setSuccess(''); void previewQuery.refetch() }
  const exportReport = (format: 'csv' | 'pdf') => { setSuccess(''); exportMutation.mutate({ filters, format }, { onSuccess: (blob) => { const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `communityai-report-${new Date().toISOString().slice(0, 10)}.${format}`; link.click(); URL.revokeObjectURL(url); setSuccess(`${format.toUpperCase()} exporté.`) } }) }
  const error = previewQuery.error?.message ?? exportMutation.error?.message
  return <main className="analytics-page-wrapper reporting-page"><div className="analytics-page-header"><div className="analytics-title-group"><h1 className="analytics-main-title">Reporting</h1><p className="analytics-subtitle">Transformez vos données Analytics en rapports exploitables.</p></div>{previewQuery.data && <ReportExportButtons onExport={exportReport} isExporting={exportMutation.isPending} error={exportMutation.error?.message} success={success} />}</div><ReportFilters filters={filters} accounts={accounts} onChange={setFilters} onPreview={preview} isLoading={previewQuery.isFetching} />{error && <div className="inbox-banner-alert banner-error">{error}</div>}{previewQuery.isLoading && <div className="analytics-loading-state"><p>Génération du rapport...</p></div>}{previewQuery.data ? <ReportPreview report={previewQuery.data} /> : !previewQuery.isFetching && <ReportEmptyState />}</main>
}