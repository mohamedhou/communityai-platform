interface AnalyticsEmptyStateProps {
  onSeedMock: () => void
  isSeeding?: boolean
}

export function AnalyticsEmptyState({ onSeedMock, isSeeding = false }: AnalyticsEmptyStateProps) {
  return (
    <div className="analytics-empty-state">
      <div className="analytics-empty-icon">📊</div>
      <h3>Aucune statistique disponible</h3>
      <p>
        Connectez vos comptes sociaux ou générez des données de démonstration pour visualiser
        l'ensemble des indicateurs de performance et graphiques d'évolution.
      </p>
      <div className="analytics-empty-actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={onSeedMock}
          disabled={isSeeding}
        >
          {isSeeding ? 'Génération en cours...' : 'Générer des données démo (30 jours)'}
        </button>
      </div>
    </div>
  )
}
