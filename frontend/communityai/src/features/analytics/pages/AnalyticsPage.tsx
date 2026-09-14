import { useState } from 'react'

import { AnalyticsEmptyState } from '../components/AnalyticsEmptyState'
import { AnalyticsFilters } from '../components/AnalyticsFilters'
import { EngagementChart } from '../components/EngagementChart'
import { KpiCard } from '../components/KpiCard'
import { PerformanceChart } from '../components/PerformanceChart'
import { TopPostsTable } from '../components/TopPostsTable'
import { useAnalytics } from '../hooks/useAnalytics'

export function AnalyticsPage() {
  const {
    filters,
    setFilters,
    accounts,
    summary,
    timeSeries,
    topPosts,
    isLoading,
    isError,
    error,
    refetchAll,
    seedMock,
    isSeeding,
  } = useAnalytics()

  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleSeedMock = async () => {
    try {
      setNotification(null)
      const res = await seedMock(filters.days || 30)
      setNotification({
        type: 'success',
        message: res.message || 'Données de démonstration générées avec succès !',
      })
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.message || 'Impossible de générer les données démo.',
      })
    }
  }

  const kpis = summary?.kpis

  const formatDateRange = () => {
    if (!summary?.period_start || !summary?.period_end) return ''
    try {
      const d1 = new Date(summary.period_start)
      const d2 = new Date(summary.period_end)
      return `${d1.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' })} au ${d2.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric', year: 'numeric' })}`
    } catch {
      return `${summary.period_start} - ${summary.period_end}`
    }
  }

  const hasData = Boolean(timeSeries.length > 0 || (kpis && (kpis.total_followers > 0 || kpis.total_reach > 0)))

  return (
    <div className="analytics-page-wrapper">
      {/* Page Header */}
      <div className="analytics-page-header">
        <div className="analytics-title-group">
          <div className="analytics-title-row">
            <h1 className="analytics-main-title">📊 Analytics &amp; Reporting</h1>
            {summary?.period_start && (
              <span className="analytics-period-badge">
                📅 {formatDateRange()}
              </span>
            )}
          </div>
          <p className="analytics-subtitle">
            Mesurez l'impact de vos publications, analysez la croissance de votre communauté et optimisez votre stratégie social media.
          </p>
        </div>
      </div>

      {notification && (
        <div className={`inbox-banner-alert ${notification.type === 'success' ? 'banner-success' : 'banner-error'}`}>
          <span>{notification.message}</span>
          <button type="button" onClick={() => setNotification(null)} className="banner-close-btn">
            ✕
          </button>
        </div>
      )}

      {isError && (
        <div className="inbox-banner-alert banner-error">
          <span>Erreur : {(error as Error)?.message || 'Échec du chargement des statistiques'}</span>
          <button type="button" onClick={refetchAll} className="btn btn-sm btn-secondary">
            Réessayer
          </button>
        </div>
      )}

      {/* Filters bar */}
      <AnalyticsFilters
        filters={filters}
        onChange={setFilters}
        accounts={accounts}
        onRefresh={refetchAll}
        onSeedMock={handleSeedMock}
        isSeeding={isSeeding}
      />

      {isLoading && !hasData ? (
        <div className="analytics-loading-state">
          <div className="spinner-medium" />
          <p>Chargement des métriques et indicateurs clés...</p>
        </div>
      ) : !hasData ? (
        <AnalyticsEmptyState onSeedMock={handleSeedMock} isSeeding={isSeeding} />
      ) : (
        <>
          {/* KPI Cards Grid */}
          {kpis && (
            <div className="kpi-grid">
              <KpiCard
                title="Abonnés Totaux"
                value={kpis.total_followers}
                icon="👥"
                trend={kpis.follower_growth}
                trendLabel="nouveaux abonnés"
                colorTheme="emerald"
              />
              <KpiCard
                title="Portée Totale (Reach)"
                value={kpis.total_reach}
                icon="📡"
                subtitle="Personnes uniques atteintes"
                colorTheme="indigo"
              />
              <KpiCard
                title="Impressions"
                value={kpis.total_impressions}
                icon="👁️"
                subtitle="Affichages cumulés"
                colorTheme="blue"
              />
              <KpiCard
                title="Engagement Total"
                value={kpis.total_engagement}
                icon="⚡"
                subtitle="Likes, comm., partages, clics"
                colorTheme="amber"
              />
              <KpiCard
                title="Taux d'Engagement"
                value={`${kpis.engagement_rate}%`}
                icon="🎯"
                subtitle="Engagement / Portée"
                colorTheme="purple"
              />
              <KpiCard
                title="Publications"
                value={kpis.posts_published}
                icon="📝"
                subtitle="Posts publiés sur la période"
                colorTheme="rose"
              />
            </div>
          )}

          {/* Charts Row */}
          <div className="analytics-charts-grid">
            <PerformanceChart points={timeSeries} />
            {kpis && <EngagementChart kpis={kpis} />}
          </div>

          {/* Top Posts Table */}
          <TopPostsTable posts={topPosts} />
        </>
      )}
    </div>
  )
}
