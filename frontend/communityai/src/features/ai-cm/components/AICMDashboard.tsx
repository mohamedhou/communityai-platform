import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import { getAICMDashboard } from '../services/aiCmApi'
import type { AICMDashboardMetrics } from '../types'

export function AICMDashboard() {
  const { accessToken } = useAuth()
  const [metrics, setMetrics] = useState<AICMDashboardMetrics | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const [platformFilter, setPlatformFilter] = useState<string>('ALL')
  const [dateRange, setDateRange] = useState<string>('30')

  const fetchDashboard = useCallback(async () => {
    if (!accessToken) return
    setLoading(true)
    setError(null)

    try {
      let startDateStr: string | undefined
      if (dateRange === '7') {
        const d = new Date()
        d.setDate(d.getDate() - 7)
        startDateStr = d.toISOString()
      } else if (dateRange === '30') {
        const d = new Date()
        d.setDate(d.getDate() - 30)
        startDateStr = d.toISOString()
      }

      const data = await getAICMDashboard(
        accessToken,
        platformFilter === 'ALL' ? undefined : platformFilter,
        startDateStr,
      )
      setMetrics(data)
    } catch (err: any) {
      setError(err.message || 'Impossible de charger les métriques du tableau de bord.')
    } finally {
      setLoading(false)
    }
  }, [accessToken, platformFilter, dateRange])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  if (loading && !metrics) {
    return (
      <div className="aicm-loading-container">
        <div className="aicm-spinner" />
        <p>Calcul des métriques opérationnelles en temps réel...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="aicm-error-card">
        <h3>Erreur de chargement</h3>
        <p>{error}</p>
        <button type="button" className="btn btn-outline" onClick={fetchDashboard}>
          Réessayer
        </button>
      </div>
    )
  }

  if (!metrics) return null

  const totalAnalyzed = metrics.total_comments_analyzed + metrics.total_messages_analyzed
  const sTotal =
    metrics.sentiment_breakdown.positive +
    metrics.sentiment_breakdown.neutral +
    metrics.sentiment_breakdown.negative
  const posPct = sTotal > 0 ? Math.round((metrics.sentiment_breakdown.positive / sTotal) * 100) : 0
  const neuPct = sTotal > 0 ? Math.round((metrics.sentiment_breakdown.neutral / sTotal) * 100) : 0
  const negPct = sTotal > 0 ? Math.round((metrics.sentiment_breakdown.negative / sTotal) * 100) : 0

  return (
    <div className="aicm-dashboard-view">
      {/* Filters Bar */}
      <div className="aicm-filters-bar">
        <div className="aicm-filter-group">
          <span className="aicm-filter-label">Réseau :</span>
          <div className="aicm-pill-selector">
            {[
              { id: 'ALL', label: 'Tous' },
              { id: 'facebook', label: 'Facebook' },
              { id: 'instagram', label: 'Instagram' },
              { id: 'linkedin', label: 'LinkedIn' },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                className={`aicm-pill ${platformFilter === p.id ? 'active' : ''}`}
                onClick={() => setPlatformFilter(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="aicm-filter-group">
          <span className="aicm-filter-label">Période :</span>
          <select
            className="aicm-select"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
          >
            <option value="7">7 derniers jours</option>
            <option value="30">30 derniers jours</option>
            <option value="ALL">Tout l'historique</option>
          </select>
          <button type="button" className="btn btn-secondary btn-sm" onClick={fetchDashboard}>
            🔄 Actualiser
          </button>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="aicm-kpi-grid">
        <div className="aicm-kpi-card card-highlight">
          <div className="kpi-header">
            <span className="kpi-icon">💬</span>
            <span className="kpi-tag">Total Analysé</span>
          </div>
          <div className="kpi-value">{totalAnalyzed}</div>
          <div className="kpi-sub">
            {metrics.total_comments_analyzed} commentaires • {metrics.total_messages_analyzed} messages directs
          </div>
        </div>

        <div className="aicm-kpi-card">
          <div className="kpi-header">
            <span className="kpi-icon">🤖</span>
            <span className="kpi-tag">Réponses IA</span>
          </div>
          <div className="kpi-value">{metrics.replies_generated}</div>
          <div className="kpi-sub">
            <span className="text-success">{metrics.replies_sent} envoyées</span> •{' '}
            <span className="text-warning">{metrics.replies_pending_approval} en attente</span>
          </div>
        </div>

        <div className="aicm-kpi-card">
          <div className="kpi-header">
            <span className="kpi-icon">🎯</span>
            <span className="kpi-tag">Taux de Résolution</span>
          </div>
          <div className="kpi-value">{metrics.resolution_rate}%</div>
          <div className="kpi-sub">
            {metrics.average_response_time_seconds
              ? `Temps moyen : ${Math.round(metrics.average_response_time_seconds / 60)} min`
              : 'Délai moyen non calculé'}
          </div>
        </div>

        <div className="aicm-kpi-card card-urgent">
          <div className="kpi-header">
            <span className="kpi-icon">🚨</span>
            <span className="kpi-tag">Urgences & Escalades</span>
          </div>
          <div className="kpi-value text-danger">{metrics.urgent_messages_count}</div>
          <div className="kpi-sub">
            {metrics.escalated_conversations_count} conversations transférées à un humain
          </div>
        </div>
      </div>

      {/* Analytical Charts Grid */}
      <div className="aicm-charts-grid">
        {/* Sentiment Breakdown Card */}
        <div className="aicm-chart-card">
          <div className="chart-card-header">
            <h3>📊 Répartition des Sentiments</h3>
            <span className="chart-badge">{sTotal} interactions classées</span>
          </div>

          <div className="sentiment-bars-container">
            <div className="sentiment-row">
              <div className="sentiment-label-group">
                <span className="sentiment-dot positive" />
                <span className="sentiment-name">Positif</span>
                <span className="sentiment-count">({metrics.sentiment_breakdown.positive})</span>
              </div>
              <div className="sentiment-bar-track">
                <div className="sentiment-bar-fill positive" style={{ width: `${posPct}%` }} />
              </div>
              <span className="sentiment-pct">{posPct}%</span>
            </div>

            <div className="sentiment-row">
              <div className="sentiment-label-group">
                <span className="sentiment-dot neutral" />
                <span className="sentiment-name">Neutre</span>
                <span className="sentiment-count">({metrics.sentiment_breakdown.neutral})</span>
              </div>
              <div className="sentiment-bar-track">
                <div className="sentiment-bar-fill neutral" style={{ width: `${neuPct}%` }} />
              </div>
              <span className="sentiment-pct">{neuPct}%</span>
            </div>

            <div className="sentiment-row">
              <div className="sentiment-label-group">
                <span className="sentiment-dot negative" />
                <span className="sentiment-name">Négatif</span>
                <span className="sentiment-count">({metrics.sentiment_breakdown.negative})</span>
              </div>
              <div className="sentiment-bar-track">
                <div className="sentiment-bar-fill negative" style={{ width: `${negPct}%` }} />
              </div>
              <span className="sentiment-pct">{negPct}%</span>
            </div>
          </div>
        </div>

        {/* Intent Breakdown Card */}
        <div className="aicm-chart-card">
          <div className="chart-card-header">
            <h3>🎯 Intentions Clients Détectées</h3>
            <span className="chart-badge">Analyse sémantique</span>
          </div>

          <div className="intent-grid">
            {[
              { label: 'Questions', count: metrics.intent_breakdown.question, icon: '❓' },
              { label: 'Compliments', count: metrics.intent_breakdown.compliment, icon: '🌟' },
              { label: 'Réclamations', count: metrics.intent_breakdown.complaint, icon: '⚠️', isWarning: true },
              { label: 'Tarifs & Prix', count: metrics.intent_breakdown.price_inquiry, icon: '💶' },
              { label: 'Demandes Achat', count: metrics.intent_breakdown.purchase, icon: '🛒' },
              { label: 'Livraison & Suivi', count: metrics.intent_breakdown.delivery_inquiry, icon: '📦' },
              { label: 'Support Technique', count: metrics.intent_breakdown.support_request, icon: '🛠️' },
              { label: 'Spam & Risques', count: metrics.intent_breakdown.spam, icon: '🚫' },
            ].map((it) => (
              <div key={it.label} className={`intent-card ${it.isWarning && it.count > 0 ? 'warning' : ''}`}>
                <div className="intent-icon">{it.icon}</div>
                <div className="intent-info">
                  <span className="intent-name">{it.label}</span>
                  <span className="intent-count">{it.count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
