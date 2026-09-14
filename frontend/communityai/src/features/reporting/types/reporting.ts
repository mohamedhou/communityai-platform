import type { AnalyticsKpiSummary, AnalyticsTimeSeriesPoint, TopPostMetric } from '../../analytics/types/analytics'

export interface ReportFilters {
  social_account_id?: number
  platform?: string
  start_date: string
  end_date: string
}

export interface ReportPreview {
  report_title: string
  workspace_name: string
  period_start: string
  period_end: string
  platform: string | null
  accounts: string[]
  kpis: AnalyticsKpiSummary
  time_series: AnalyticsTimeSeriesPoint[]
  engagement_breakdown: Record<string, number>
  top_posts: TopPostMetric[]
  generated_at: string
}