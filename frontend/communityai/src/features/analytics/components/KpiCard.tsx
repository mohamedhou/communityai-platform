interface KpiCardProps {
  title: string
  value: string | number
  icon: string
  subtitle?: string
  trend?: number
  trendLabel?: string
  colorTheme?: 'blue' | 'indigo' | 'emerald' | 'amber' | 'purple' | 'rose'
}

export function KpiCard({
  title,
  value,
  icon,
  subtitle,
  trend,
  trendLabel = 'sur la période',
  colorTheme = 'blue',
}: KpiCardProps) {
  const isPositive = trend !== undefined && trend > 0
  const isNegative = trend !== undefined && trend < 0

  const formatNumber = (val: string | number) => {
    if (typeof val === 'number') {
      return val.toLocaleString('fr-FR')
    }
    return val
  }

  return (
    <div className={`kpi-card kpi-theme-${colorTheme}`}>
      <div className="kpi-card-header">
        <span className="kpi-card-title">{title}</span>
        <div className="kpi-card-icon-wrapper">
          <span className="kpi-card-icon">{icon}</span>
        </div>
      </div>

      <div className="kpi-card-body">
        <div className="kpi-card-value">{formatNumber(value)}</div>

        {trend !== undefined ? (
          <div className="kpi-trend-row">
            <span
              className={`kpi-trend-badge ${
                isPositive ? 'trend-up' : isNegative ? 'trend-down' : 'trend-neutral'
              }`}
            >
              {isPositive ? '↗ +' : isNegative ? '↘ ' : '→ '}
              {formatNumber(trend)}
            </span>
            <span className="kpi-trend-label">{trendLabel}</span>
          </div>
        ) : subtitle ? (
          <div className="kpi-card-subtitle">{subtitle}</div>
        ) : null}
      </div>
    </div>
  )
}
