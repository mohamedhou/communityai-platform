import { PerformanceChart } from '../../analytics/components/PerformanceChart'
import type { AnalyticsTimeSeriesPoint } from '../../analytics/types/analytics'

export function ReportPerformanceSection({ points }: { points: AnalyticsTimeSeriesPoint[] }) { return <section className="report-section"><PerformanceChart points={points} /></section> }