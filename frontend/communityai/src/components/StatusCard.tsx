import type { ReactNode } from 'react'

type StatusCardProps = {
  title: string
  value: ReactNode
  hint?: string
}

export function StatusCard({ title, value, hint }: StatusCardProps) {
  return (
    <article className="status-card">
      <p className="status-card__title">{title}</p>
      <div className="status-card__value">{value}</div>
      {hint ? <p className="status-card__hint">{hint}</p> : null}
    </article>
  )
}
