import { useState } from 'react'
import { AICMDashboard } from '../components/AICMDashboard'
import { BusinessKnowledgeManager } from '../components/BusinessKnowledgeManager'
import { AICMSettingsView } from '../components/AICMSettingsView'
import { AICMAuditLogsView } from '../components/AICMAuditLogsView'

type MainTab = 'dashboard' | 'knowledge' | 'settings' | 'audit'

export function AICMHubPage() {
  const [activeTab, setActiveTab] = useState<MainTab>('dashboard')

  return (
    <div className="aicm-hub-page">
      {/* Page Title & Hero */}
      <div className="aicm-hero-header">
        <div className="aicm-hero-content">
          <div className="aicm-hero-badge">⚡ Module Intelligent</div>
          <h1 className="aicm-hero-title">AI Community Manager</h1>
          <p className="aicm-hero-subtitle">
            Système d'assistance intelligent qui comprend les besoins clients, exploite la base de connaissances vérifiée de votre entreprise et génère des réponses fiables et personnalisées.
          </p>
        </div>

        {/* Global Tab Switcher */}
        <div className="aicm-hero-tabs">
          <button
            type="button"
            className={`hero-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Tableau de bord
          </button>
          <button
            type="button"
            className={`hero-tab-btn ${activeTab === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActiveTab('knowledge')}
          >
            🧠 Base de connaissances
          </button>
          <button
            type="button"
            className={`hero-tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ Règles & Automatisation
          </button>
          <button
            type="button"
            className={`hero-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            📜 Journal d'audit
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="aicm-content-container">
        {activeTab === 'dashboard' && <AICMDashboard />}
        {activeTab === 'knowledge' && <BusinessKnowledgeManager />}
        {activeTab === 'settings' && <AICMSettingsView />}
        {activeTab === 'audit' && <AICMAuditLogsView />}
      </div>
    </div>
  )
}
