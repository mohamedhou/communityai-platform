import { useState } from 'react'
import type { SocialAccount } from '../../social-accounts/types/social'
import type { AnalyticsFiltersState } from '../types/analytics'

interface AnalyticsFiltersProps {
  filters: AnalyticsFiltersState
  onChange: (filters: AnalyticsFiltersState) => void
  accounts: SocialAccount[]
  onRefresh: () => void
  onSeedMock: () => void
  isSeeding?: boolean
}

export function AnalyticsFilters({
  filters,
  onChange,
  accounts,
  onRefresh,
  onSeedMock,
  isSeeding = false,
}: AnalyticsFiltersProps) {
  const [showCustomDates, setShowCustomDates] = useState(false)

  const handlePlatformChange = (platform: string) => {
    onChange({
      ...filters,
      platform,
      social_account_id: 'ALL', // Reset account selection if platform changes
    })
  }

  const handleAccountChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    onChange({
      ...filters,
      social_account_id: val === 'ALL' ? 'ALL' : Number(val),
    })
  }

  const handleDaysChange = (days: number) => {
    setShowCustomDates(false)
    onChange({
      ...filters,
      days,
      start_date: undefined,
      end_date: undefined,
    })
  }

  const handleCustomDateChange = (start?: string, end?: string) => {
    onChange({
      ...filters,
      days: undefined,
      start_date: start !== undefined ? start : filters.start_date,
      end_date: end !== undefined ? end : filters.end_date,
    })
  }

  const currentPlatform = filters.platform || 'ALL'
  const currentDays = filters.days || 30

  // Filter accounts by active platform if platform is selected
  const visibleAccounts = accounts.filter((acc) => {
    if (currentPlatform === 'ALL') return true
    const p = currentPlatform.toLowerCase()
    return acc.platform?.toLowerCase() === p || acc.provider?.toLowerCase() === p
  })

  return (
    <div className="analytics-filters-bar">
      <div className="analytics-filters-left">
        {/* Platform selection pills */}
        <div className="filter-block">
          <span className="filter-block-label">Plateforme :</span>
          <div className="filter-pills">
            <button
              type="button"
              className={`pill-btn ${currentPlatform === 'ALL' ? 'active' : ''}`}
              onClick={() => handlePlatformChange('ALL')}
            >
              🌐 Toutes
            </button>
            <button
              type="button"
              className={`pill-btn ${currentPlatform.toLowerCase() === 'meta' ? 'active' : ''}`}
              onClick={() => handlePlatformChange('meta')}
            >
              Meta
            </button>
            <button
              type="button"
              className={`pill-btn ${currentPlatform.toLowerCase() === 'linkedin' ? 'active' : ''}`}
              onClick={() => handlePlatformChange('linkedin')}
            >
              LinkedIn
            </button>
          </div>
        </div>

        {/* Social account dropdown */}
        <div className="filter-block">
          <span className="filter-block-label">Compte :</span>
          <select
            value={filters.social_account_id || 'ALL'}
            onChange={handleAccountChange}
            className="analytics-select-input"
          >
            <option value="ALL">Tous les comptes ({visibleAccounts.length})</option>
            {visibleAccounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.account_name} ({acc.platform.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        {/* Period preset buttons */}
        <div className="filter-block">
          <span className="filter-block-label">Période :</span>
          <div className="filter-pills">
            <button
              type="button"
              className={`pill-btn ${!showCustomDates && currentDays === 7 ? 'active' : ''}`}
              onClick={() => handleDaysChange(7)}
            >
              7 jours
            </button>
            <button
              type="button"
              className={`pill-btn ${!showCustomDates && currentDays === 14 ? 'active' : ''}`}
              onClick={() => handleDaysChange(14)}
            >
              14 jours
            </button>
            <button
              type="button"
              className={`pill-btn ${!showCustomDates && currentDays === 30 ? 'active' : ''}`}
              onClick={() => handleDaysChange(30)}
            >
              30 jours
            </button>
            <button
              type="button"
              className={`pill-btn ${!showCustomDates && currentDays === 90 ? 'active' : ''}`}
              onClick={() => handleDaysChange(90)}
            >
              90 jours
            </button>
            <button
              type="button"
              className={`pill-btn ${showCustomDates ? 'active' : ''}`}
              onClick={() => setShowCustomDates(!showCustomDates)}
            >
              📅 Personnalisé
            </button>
          </div>
        </div>

        {/* Custom date range inputs */}
        {showCustomDates && (
          <div className="filter-block custom-dates-block">
            <input
              type="date"
              value={filters.start_date || ''}
              onChange={(e) => handleCustomDateChange(e.target.value, undefined)}
              className="analytics-date-input"
            />
            <span className="date-separator">au</span>
            <input
              type="date"
              value={filters.end_date || ''}
              onChange={(e) => handleCustomDateChange(undefined, e.target.value)}
              className="analytics-date-input"
            />
          </div>
        )}
      </div>

      <div className="analytics-filters-right">
        <button
          type="button"
          className="btn btn-secondary btn-icon-only"
          onClick={onRefresh}
          title="Rafraîchir les données"
        >
          🔄
        </button>

        <button
          type="button"
          className="btn btn-outline"
          onClick={onSeedMock}
          disabled={isSeeding}
          title="Générer 30 jours de données simulées pour vos comptes"
        >
          {isSeeding ? 'Génération...' : '🧪 Données démo'}
        </button>
      </div>
    </div>
  )
}
