import { useState, useMemo } from 'react'
import type { AnalyticsTimeSeriesPoint } from '../types/analytics'

interface PerformanceChartProps {
  points: AnalyticsTimeSeriesPoint[]
}

type MetricKey = 'reach' | 'impressions' | 'followers' | 'engagement'

interface MetricConfig {
  key: MetricKey
  label: string
  color: string
  gradientId: string
}

const METRICS: MetricConfig[] = [
  { key: 'reach', label: 'Portée', color: '#6366f1', gradientId: 'reachGrad' },
  { key: 'impressions', label: 'Impressions', color: '#3b82f6', gradientId: 'impGrad' },
  { key: 'followers', label: 'Abonnés', color: '#10b981', gradientId: 'follGrad' },
  { key: 'engagement', label: 'Engagement', color: '#f59e0b', gradientId: 'engGrad' },
]

export function PerformanceChart({ points }: PerformanceChartProps) {
  const [activeMetrics, setActiveMetrics] = useState<Record<MetricKey, boolean>>({
    reach: true,
    impressions: true,
    followers: false,
    engagement: true,
  })

  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  const toggleMetric = (key: MetricKey) => {
    setActiveMetrics((prev) => {
      // Ensure at least one metric remains active
      const next = { ...prev, [key]: !prev[key] }
      if (!Object.values(next).some(Boolean)) return prev
      return next
    })
  }

  // Chart dimensions
  const width = 800
  const height = 320
  const padding = { top: 20, right: 30, bottom: 40, left: 60 }
  const innerWidth = width - padding.left - padding.right
  const innerHeight = height - padding.top - padding.bottom

  const maxVal = useMemo(() => {
    if (!points.length) return 100
    let m = 0
    for (const p of points) {
      for (const mConf of METRICS) {
        if (activeMetrics[mConf.key]) {
          const v = p[mConf.key]
          if (v > m) m = v
        }
      }
    }
    return m > 0 ? Math.ceil(m * 1.1) : 100
  }, [points, activeMetrics])

  const getY = (val: number) => {
    return padding.top + innerHeight - (val / maxVal) * innerHeight
  }

  const getX = (index: number) => {
    if (points.length <= 1) return padding.left + innerWidth / 2
    return padding.left + (index / (points.length - 1)) * innerWidth
  }

  // Generate SVG paths
  const generatePath = (key: MetricKey) => {
    if (!points.length) return ''
    return points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p[key])}`)
      .join(' ')
  }

  const generateAreaPath = (key: MetricKey) => {
    if (!points.length) return ''
    const line = points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p[key])}`)
      .join(' ')
    const bottom = padding.top + innerHeight
    return `${line} L ${getX(points.length - 1)} ${bottom} L ${getX(0)} ${bottom} Z`
  }

  // Format date ticks
  const xTicks = useMemo(() => {
    if (points.length <= 6) return points.map((p, i) => ({ index: i, date: p.date }))
    const step = Math.ceil(points.length / 6)
    const ticks = []
    for (let i = 0; i < points.length; i += step) {
      ticks.push({ index: i, date: points[i].date })
    }
    if (ticks[ticks.length - 1].index !== points.length - 1) {
      ticks.push({ index: points.length - 1, date: points[points.length - 1].date })
    }
    return ticks
  }, [points])

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((pct) => ({
    val: Math.round(maxVal * pct),
    y: padding.top + innerHeight - pct * innerHeight,
  }))

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const hoveredPoint = hoveredIndex !== null && points[hoveredIndex] ? points[hoveredIndex] : null

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <div>
          <h3 className="chart-title">📈 Évolution des Performances</h3>
          <p className="chart-subtitle">Progression journalière de votre visibilité et interaction</p>
        </div>

        {/* Series toggle buttons */}
        <div className="chart-series-toggles">
          {METRICS.map((m) => (
            <button
              key={m.key}
              type="button"
              className={`series-toggle-btn ${activeMetrics[m.key] ? 'active' : ''}`}
              style={{
                borderColor: activeMetrics[m.key] ? m.color : 'transparent',
                backgroundColor: activeMetrics[m.key] ? `${m.color}15` : '#f1f5f9',
                color: activeMetrics[m.key] ? m.color : '#64748b',
              }}
              onClick={() => toggleMetric(m.key)}
            >
              <span className="series-color-dot" style={{ backgroundColor: m.color }} />
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-svg-wrapper">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="performance-svg"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="reachGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="impGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="follGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="engGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines & Y Ticks */}
          {yTicks.map((t, idx) => (
            <g key={idx}>
              <line
                x1={padding.left}
                y1={t.y}
                x2={padding.left + innerWidth}
                y2={t.y}
                stroke="#e2e8f0"
                strokeDasharray="4 4"
              />
              <text
                x={padding.left - 10}
                y={t.y + 4}
                textAnchor="end"
                fontSize="11"
                fill="#94a3b8"
                fontFamily="inherit"
              >
                {t.val >= 1000 ? `${(t.val / 1000).toFixed(1)}k` : t.val}
              </text>
            </g>
          ))}

          {/* X Axis Date Ticks */}
          {xTicks.map((t) => (
            <text
              key={t.index}
              x={getX(t.index)}
              y={height - 12}
              textAnchor="middle"
              fontSize="11"
              fill="#94a3b8"
              fontFamily="inherit"
            >
              {formatDate(t.date)}
            </text>
          ))}

          {/* Render Active Area and Line Series */}
          {METRICS.map(
            (m) =>
              activeMetrics[m.key] && (
                <g key={m.key}>
                  <path d={generateAreaPath(m.key)} fill={`url(#${m.gradientId})`} />
                  <path
                    d={generatePath(m.key)}
                    fill="none"
                    stroke={m.color}
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </g>
              ),
          )}

          {/* Hover Vertical Line & Overlay Target Boxes */}
          {points.map((p, idx) => {
            const x = getX(idx)
            return (
              <rect
                key={p.date}
                x={x - innerWidth / (points.length * 2 || 1)}
                y={padding.top}
                width={innerWidth / (points.length || 1)}
                height={innerHeight}
                fill="transparent"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredIndex(idx)}
              />
            )
          })}

          {hoveredIndex !== null && (
            <g>
              <line
                x1={getX(hoveredIndex)}
                y1={padding.top}
                x2={getX(hoveredIndex)}
                y2={padding.top + innerHeight}
                stroke="#64748b"
                strokeWidth="1.5"
                strokeDasharray="3 3"
              />
              {METRICS.map(
                (m) =>
                  activeMetrics[m.key] &&
                  hoveredPoint && (
                    <circle
                      key={m.key}
                      cx={getX(hoveredIndex)}
                      cy={getY(hoveredPoint[m.key])}
                      r="4.5"
                      fill="#ffffff"
                      stroke={m.color}
                      strokeWidth="2.5"
                    />
                  ),
              )}
            </g>
          )}
        </svg>

        {/* Floating Tooltip Box */}
        {hoveredPoint && hoveredIndex !== null && (
          <div
            className="chart-floating-tooltip"
            style={{
              left: `${(getX(hoveredIndex) / width) * 100}%`,
              transform: getX(hoveredIndex) > width * 0.7 ? 'translateX(-105%)' : 'translateX(10px)',
            }}
          >
            <div className="tooltip-date">{formatDate(hoveredPoint.date)}</div>
            <div className="tooltip-metrics-list">
              {METRICS.map(
                (m) =>
                  activeMetrics[m.key] && (
                    <div key={m.key} className="tooltip-metric-row">
                      <span className="tooltip-dot" style={{ backgroundColor: m.color }} />
                      <span className="tooltip-label">{m.label} :</span>
                      <span className="tooltip-value">{hoveredPoint[m.key].toLocaleString('fr-FR')}</span>
                    </div>
                  ),
              )}
              <div className="tooltip-metric-row tooltip-rate-row">
                <span className="tooltip-label">Taux d'engagement :</span>
                <span className="tooltip-value font-bold">{hoveredPoint.engagement_rate}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
