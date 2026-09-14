import type { AnalyticsKpiSummary } from '../types/analytics'

interface EngagementChartProps {
  kpis: AnalyticsKpiSummary
}

export function EngagementChart({ kpis }: EngagementChartProps) {
  const total = (kpis.total_likes + kpis.total_comments + kpis.total_shares + kpis.total_clicks) || 1

  const items = [
    {
      label: 'J’aime (Likes)',
      count: kpis.total_likes,
      percentage: Math.round((kpis.total_likes / total) * 100),
      color: '#3b82f6',
      icon: '👍',
    },
    {
      label: 'Commentaires',
      count: kpis.total_comments,
      percentage: Math.round((kpis.total_comments / total) * 100),
      color: '#10b981',
      icon: '💬',
    },
    {
      label: 'Partages',
      count: kpis.total_shares,
      percentage: Math.round((kpis.total_shares / total) * 100),
      color: '#8b5cf6',
      icon: '🔄',
    },
    {
      label: 'Clics sur liens',
      count: kpis.total_clicks,
      percentage: Math.round((kpis.total_clicks / total) * 100),
      color: '#f59e0b',
      icon: '🖱️',
    },
  ]

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <div>
          <h3 className="chart-title">🎯 Répartition de l'Engagement</h3>
          <p className="chart-subtitle">Distribution des interactions générées sur la période</p>
        </div>
        <div className="engagement-total-badge">
          Total : {kpis.total_engagement.toLocaleString('fr-FR')}
        </div>
      </div>

      <div className="engagement-breakdown-wrapper">
        {/* Cumulative segment bar */}
        <div className="engagement-stacked-bar">
          {items.map(
            (it, idx) =>
              it.count > 0 && (
                <div
                  key={idx}
                  className="stacked-segment"
                  style={{
                    width: `${it.percentage}%`,
                    backgroundColor: it.color,
                  }}
                  title={`${it.label}: ${it.count.toLocaleString('fr-FR')} (${it.percentage}%)`}
                />
              ),
          )}
        </div>

        {/* Detailed item list */}
        <div className="engagement-items-grid">
          {items.map((it, idx) => (
            <div key={idx} className="engagement-item-card">
              <div className="engagement-item-header">
                <span className="engagement-item-icon">{it.icon}</span>
                <span className="engagement-item-label">{it.label}</span>
                <span className="engagement-item-pct" style={{ color: it.color }}>
                  {it.percentage}%
                </span>
              </div>
              <div className="engagement-item-count">{it.count.toLocaleString('fr-FR')}</div>
              <div className="engagement-item-progress-track">
                <div
                  className="engagement-item-progress-fill"
                  style={{
                    width: `${it.percentage}%`,
                    backgroundColor: it.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
