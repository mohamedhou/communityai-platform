export function NotificationEmptyState() {
  return (
    <div className="notification-empty-state">
      <span className="notification-empty-icon" aria-hidden="true">✓</span>
      <h2>Aucune notification</h2>
      <p>Tout est calme pour le moment.</p>
    </div>
  )
}