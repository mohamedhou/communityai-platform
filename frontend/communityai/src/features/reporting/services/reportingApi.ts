import { API_BASE_URL } from '../../../lib/env'
import type { ReportFilters, ReportPreview } from '../types/reporting'

const buildQuery = (filters: ReportFilters) => {
  const params = new URLSearchParams({ start_date: filters.start_date, end_date: filters.end_date })
  if (filters.platform) params.set('platform', filters.platform)
  if (filters.social_account_id) params.set('social_account_id', String(filters.social_account_id))
  return params.toString()
}

async function parseError(response: Response, fallback: string) {
  const payload = await response.json().catch(() => ({ detail: fallback }))
  throw new Error(typeof payload.detail === 'string' ? payload.detail : fallback)
}

export async function getReportPreview(token: string, filters: ReportFilters): Promise<ReportPreview> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reports/preview?${buildQuery(filters)}`, { headers: { Authorization: `Bearer ${token}` } })
  if (!response.ok) await parseError(response, 'Impossible de générer le rapport')
  return response.json()
}

export async function downloadReport(token: string, filters: ReportFilters, format: 'csv' | 'pdf'): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/v1/reports/export/${format}?${buildQuery(filters)}`, { headers: { Authorization: `Bearer ${token}` } })
  if (!response.ok) await parseError(response, `Impossible d'exporter le rapport en ${format.toUpperCase()}`)
  return response.blob()
}