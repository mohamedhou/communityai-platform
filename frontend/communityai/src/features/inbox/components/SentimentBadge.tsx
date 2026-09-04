import type { InboxSentiment } from '../types/inbox'

interface SentimentBadgeProps {
  sentiment: InboxSentiment
  score?: number | null
  showScore?: boolean
}

export function SentimentBadge({ sentiment, score, showScore = false }: SentimentBadgeProps) {
  let badgeClass = 'sentiment-badge-neutral'
  let label = 'Neutre'
  let icon = '😐'

  switch (sentiment) {
    case 'POSITIVE':
      badgeClass = 'sentiment-badge-positive'
      label = 'Positif'
      icon = '😊'
      break
    case 'NEGATIVE':
      badgeClass = 'sentiment-badge-negative'
      label = 'Négatif'
      icon = '😠'
      break
    case 'NEUTRAL':
      badgeClass = 'sentiment-badge-neutral'
      label = 'Neutre'
      icon = '😐'
      break
    case 'UNKNOWN':
    default:
      badgeClass = 'sentiment-badge-unknown'
      label = 'Inconnu'
      icon = '❓'
      break
  }

  const formattedScore = score !== undefined && score !== null ? (score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2)) : null

  return (
    <span className={`sentiment-badge ${badgeClass}`}>
      <span className="sentiment-icon">{icon}</span>
      <span className="sentiment-label">{label}</span>
      {showScore && formattedScore && (
        <span className="sentiment-score">({formattedScore})</span>
      )}
    </span>
  )
}
