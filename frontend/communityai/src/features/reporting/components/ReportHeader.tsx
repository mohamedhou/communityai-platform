import type { ReportPreview } from '../types/reporting'

export function ReportHeader({ report }: { report: ReportPreview }) {
  return <div className="report-preview-header"><div><p className="eyebrow">CommunityAI report</p><h2>{report.report_title}</h2><p>{report.workspace_name} · {report.period_start} → {report.period_end}</p></div><span className="report-scope-badge">{report.platform ?? 'Toutes plateformes'}</span></div>
}