import { KpiCard } from '../../analytics/components/KpiCard'
import type { AnalyticsKpiSummary } from '../../analytics/types/analytics'

export function ReportKpiGrid({ kpis }: { kpis: AnalyticsKpiSummary }) {
  return <div className="kpi-grid report-kpi-grid"><KpiCard title="Abonnés" value={kpis.total_followers} icon="👥" trend={kpis.follower_growth} trendLabel="croissance" colorTheme="emerald" /><KpiCard title="Portée" value={kpis.total_reach} icon="📡" colorTheme="indigo" /><KpiCard title="Impressions" value={kpis.total_impressions} icon="👁" colorTheme="blue" /><KpiCard title="Engagement" value={kpis.total_engagement} icon="⚡" colorTheme="amber" /><KpiCard title="Taux" value={`${kpis.engagement_rate}%`} icon="🎯" colorTheme="purple" /><KpiCard title="Publications" value={kpis.posts_published} icon="▣" colorTheme="rose" /></div>
}