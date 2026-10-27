interface AnalyticsEmptyStateProps {
  onSeedMock: () => void
  isSeeding?: boolean
  isMockMode?: boolean
}

export function AnalyticsEmptyState({ onSeedMock, isSeeding = false, isMockMode = false }: AnalyticsEmptyStateProps) {
  return (
    <div className="analytics-empty-state">
      <div className="analytics-empty-icon">📊</div>
      <h3>Aucune statistique disponible</h3>
      <p>
        Connectez vos comptes sociaux pour visualiser les indicateurs de performance et les graphiques d'évolution.
      </p>
      {isMockMode && (
        <div className="analytics-empty-actions">
          <button type="button" className="btn btn-primary" onClick={onSeedMock} disabled={isSeeding}>
            {isSeeding ? 'Génération en cours...' : 'Générer des données démo (30 jours)'}
          </button>
        </div>
      )}
    </div>
  )
}
