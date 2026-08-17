import { AppShell } from '../layouts/AppShell'
import { API_BASE_URL } from '../lib/env'
import { useHealth } from '../hooks/useHealth'
import { StatusCard } from '../components/StatusCard'

export function HomePage() {
  const health = useHealth()

  return (
    <AppShell>
      <main className="page-shell">
        <section className="hero-panel">
          <p className="eyebrow">CommunityAI</p>
          <h1>Project setup is ready.</h1>
          <p className="lead">
            Frontend, backend, PostgreSQL and Redis are wired as a clean MVP
            foundation.
          </p>
        </section>

        <section className="status-grid">
          <StatusCard
            title="Frontend"
            value="Vite + React + TypeScript"
            hint="Running from frontend/communityai"
          />
          <StatusCard
            title="Backend"
            value={health.status === 'ready' ? 'Connected' : 'Waiting'}
            hint={
              health.status === 'ready'
                ? `${health.data.service} responded on ${API_BASE_URL}`
                : health.status === 'error'
                  ? health.error
                  : 'Checking /health'
            }
          />
          <StatusCard title="Database" value="PostgreSQL" hint="Configured in Docker Compose" />
          <StatusCard title="Cache" value="Redis" hint="Prepared for future async jobs" />
        </section>
      </main>
    </AppShell>
  )
}
