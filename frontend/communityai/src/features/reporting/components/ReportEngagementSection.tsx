import { EngagementChart } from '../../analytics/components/EngagementChart'
import type { AnalyticsKpiSummary } from '../../analytics/types/analytics'

export function ReportEngagementSection({ kpis }: { kpis: AnalyticsKpiSummary }) { return <section className="report-section"><EngagementChart kpis={kpis} /></section> }