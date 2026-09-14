import type { TopPostMetric } from '../types/analytics'

interface TopPostsTableProps {
  posts: TopPostMetric[]
}

export function TopPostsTable({ posts }: TopPostsTableProps) {
  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return '-'
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('fr-FR', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  if (!posts.length) {
    return (
      <div className="top-posts-card">
        <div className="chart-card-header">
          <div>
            <h3 className="chart-title">🏆 Meilleurs Posts</h3>
            <p className="chart-subtitle">Classement de vos publications par engagement</p>
          </div>
        </div>
        <div className="top-posts-empty">
          <p>Aucune publication trouvée sur cette période.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="top-posts-card">
      <div className="chart-card-header">
        <div>
          <h3 className="chart-title">🏆 Meilleurs Posts</h3>
          <p className="chart-subtitle">Classement de vos publications les plus performantes</p>
        </div>
      </div>

      <div className="top-posts-table-responsive">
        <table className="top-posts-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}>#</th>
              <th>Publication</th>
              <th>Plateforme</th>
              <th>Date</th>
              <th>👍 Likes</th>
              <th>💬 Comm.</th>
              <th>🔄 Partages</th>
              <th>🖱️ Clics</th>
              <th>Engagement</th>
              <th>Taux</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((p, idx) => {
              const isMeta =
                p.platform.toLowerCase().includes('meta') ||
                p.platform.toLowerCase().includes('facebook') ||
                p.platform.toLowerCase().includes('instagram')

              return (
                <tr key={p.post_id}>
                  <td className="rank-cell">
                    <span className={`rank-badge ${idx < 3 ? `rank-${idx + 1}` : ''}`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="post-content-cell">
                    <p className="post-snippet-text">{p.content}</p>
                  </td>
                  <td>
                    <span className={`platform-tag ${isMeta ? 'platform-meta' : 'platform-linkedin'}`}>
                      {p.platform.toUpperCase()}
                    </span>
                  </td>
                  <td className="date-cell">{formatDate(p.published_at)}</td>
                  <td className="stat-cell">{p.likes.toLocaleString('fr-FR')}</td>
                  <td className="stat-cell">{p.comments.toLocaleString('fr-FR')}</td>
                  <td className="stat-cell">{p.shares.toLocaleString('fr-FR')}</td>
                  <td className="stat-cell">{p.clicks.toLocaleString('fr-FR')}</td>
                  <td className="stat-cell font-bold">{p.engagement.toLocaleString('fr-FR')}</td>
                  <td>
                    <span className="engagement-rate-pill">{p.engagement_rate}%</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
