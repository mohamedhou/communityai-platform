import { Link } from 'react-router-dom'
import { AppShell } from '../layouts/AppShell'
import { useAuth } from '../features/auth/hooks/useAuth'
import { useHealth } from '../hooks/useHealth'

const QUICK_ACTIONS = [
  { label: 'New Post', href: '/posts/new', icon: '✍️', color: 'var(--ca-primary)', bg: 'var(--ca-primary-light)' },
  { label: 'AI Assistant', href: '/ai', icon: '🤖', color: '#7c3aed', bg: '#ede9fe' },
  { label: 'Analytics', href: '/analytics', icon: '📊', color: '#0891b2', bg: '#ecfeff' },
  { label: 'Social Accounts', href: '/social-accounts', icon: '🔗', color: '#059669', bg: '#ecfdf5' },
  { label: 'Calendar', href: '/calendar', icon: '🗓️', color: '#d97706', bg: '#fffbeb' },
  { label: 'Inbox', href: '/inbox', icon: '💬', color: '#dc2626', bg: '#fef2f2' },
]

export function HomePage() {
  const health = useHealth()
  const { user } = useAuth()
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  return (
    <AppShell>
      <main className="page-shell">
        {/* Welcome Hero */}
        <section className="home-hero">
          <div className="home-hero-content">
            <div className="home-eyebrow">CommunityAI Platform</div>
            <h1 className="home-greeting">
              {greeting}, {user?.first_name ?? 'there'} 👋
            </h1>
            <p className="home-lead">
              Manage your social media presence, collaborate with your team, and publish content smarter with AI.
            </p>
            <div className="home-hero-badges">
              <span className="home-badge home-badge-role">{user?.role}</span>
              <span className={`home-badge ${health.status === 'ready' ? 'home-badge-online' : 'home-badge-offline'}`}>
                {health.status === 'ready' ? '● Connected' : '○ Connecting...'}
              </span>
            </div>
          </div>
          <div className="home-hero-graphic" aria-hidden="true">
            <div className="home-glow-orb home-orb-1" />
            <div className="home-glow-orb home-orb-2" />
          </div>
        </section>

        {/* Quick Actions */}
        <section className="home-section">
          <h2 className="home-section-title">Quick Actions</h2>
          <div className="home-quick-grid">
            {QUICK_ACTIONS.map((action) => (
              <Link key={action.href} to={action.href} className="home-action-card">
                <span
                  className="home-action-icon"
                  style={{ background: action.bg, color: action.color }}
                >
                  {action.icon}
                </span>
                <span className="home-action-label">{action.label}</span>
                <span className="home-action-arrow">→</span>
              </Link>
            ))}
          </div>
        </section>

        {/* System Status */}
        <section className="home-section">
          <h2 className="home-section-title">System Status</h2>
          <div className="status-grid">
            <div className="status-card">
              <p className="status-card__title">Frontend</p>
              <p className="status-card__value">Vite + React</p>
              <p className="status-card__hint">TypeScript · Running on port 5173</p>
            </div>
            <div className="status-card">
              <p className="status-card__title">Backend API</p>
              <p className="status-card__value">
                {health.status === 'ready' ? '✅ Connected' : health.status === 'error' ? '❌ Error' : '⏳ Checking...'}
              </p>
              <p className="status-card__hint">
                {health.status === 'ready'
                  ? `FastAPI · ${health.data.service}`
                  : health.status === 'error'
                    ? health.error
                    : 'Connecting to backend...'}
              </p>
            </div>
            <div className="status-card">
              <p className="status-card__title">Database</p>
              <p className="status-card__value">PostgreSQL</p>
              <p className="status-card__hint">Alembic migrations · workspace isolation enabled</p>
            </div>
            <div className="status-card">
              <p className="status-card__title">Cache</p>
              <p className="status-card__value">Redis</p>
              <p className="status-card__hint">Session store · notification bus</p>
            </div>
          </div>
        </section>
      </main>
    </AppShell>
  )
}
