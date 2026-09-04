interface InboxEmptyStateProps {
  hasFilters: boolean
  onResetFilters?: () => void
  onSeedMock?: () => void
  isSeeding?: boolean
}

export function InboxEmptyState({
  hasFilters,
  onResetFilters,
  onSeedMock,
  isSeeding = false,
}: InboxEmptyStateProps) {
  return (
    <div className="inbox-empty-state">
      <div className="inbox-empty-icon">📥</div>
      <h3>{hasFilters ? 'Aucune interaction trouvée' : 'Boîte de réception vide'}</h3>
      <p>
        {hasFilters
          ? 'Aucun message ou commentaire ne correspond à vos filtres actuels.'
          : 'Vous êtes à jour ! Aucune nouvelle interaction nécessitant votre attention.'}
      </p>
      <div className="inbox-empty-actions">
        {hasFilters && onResetFilters && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onResetFilters}
          >
            Réinitialiser les filtres
          </button>
        )}
        {onSeedMock && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={onSeedMock}
            disabled={isSeeding}
          >
            {isSeeding ? 'Génération en cours...' : 'Générer des interactions démo'}
          </button>
        )}
      </div>
    </div>
  )
}
