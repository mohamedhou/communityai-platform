import { ReportEngagementSection } from './ReportEngagementSection'
import { ReportHeader } from './ReportHeader'
import { ReportKpiGrid } from './ReportKpiGrid'
import { ReportPerformanceSection } from './ReportPerformanceSection'
import { ReportTopPosts } from './ReportTopPosts'
import type { ReportPreview as ReportPreviewData } from '../types/reporting'

export function ReportPreview({ report }: { report: ReportPreviewData }) {
  return <div className="report-preview"><ReportHeader report={report} /><ReportKpiGrid kpis={report.kpis} /><div className="analytics-charts-grid"><ReportPerformanceSection points={report.time_series} /><ReportEngagementSection kpis={report.kpis} /></div><ReportTopPosts posts={report.top_posts} /><p className="report-generated-at">Generated {new Date(report.generated_at).toLocaleString('fr-FR')}</p></div>
}