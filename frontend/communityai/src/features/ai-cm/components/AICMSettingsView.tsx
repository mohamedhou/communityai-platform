import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import { getAICMSettings, updateAICMSettings } from '../services/aiCmApi'
import type { AICMMode, AICMSettings } from '../types'

export function AICMSettingsView() {
  const { accessToken } = useAuth()
  const [settings, setSettings] = useState<AICMSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const loadSettings = useCallback(async () => {
    if (!accessToken) return
    setLoading(true)
    try {
      const data = await getAICMSettings(accessToken)
      setSettings(data)
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Impossible de charger les paramètres.' })
    } finally {
      setLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  const showToast = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 4000)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!accessToken || !settings) return
    setSaving(true)
    try {
      const updated = await updateAICMSettings(accessToken, settings)
      setSettings(updated)
      showToast('success', 'Règles d’automatisation mises à jour avec succès !')
    } catch (err: any) {
      showToast('error', err.message || 'Erreur lors de la sauvegarde.')
    } finally {
      setSaving(false)
    }
  }

  if (loading && !settings) {
    return (
      <div className="aicm-loading-container">
        <div className="aicm-spinner" />
        <p>Chargement des règles d'automatisation...</p>
      </div>
    )
  }

  if (!settings) return null

  const handlePlatformToggle = (platform: string) => {
    const current = settings.enabled_platforms || []
    const updated = current.includes(platform)
      ? current.filter((p) => p !== platform)
      : [...current, platform]
    setSettings({ ...settings, enabled_platforms: updated })
  }

  const handleIntentToggle = (intent: string) => {
    const current = settings.auto_reply_intents || []
    const updated = current.includes(intent)
      ? current.filter((i) => i !== intent)
      : [...current, intent]
    setSettings({ ...settings, auto_reply_intents: updated })
  }

  return (
    <div className="aicm-settings-view">
      {notification && (
        <div className={`aicm-alert alert-${notification.type}`}>
          {notification.type === 'success' ? '✅' : '⚠️'} {notification.message}
        </div>
      )}

      <form onSubmit={handleSave} className="aicm-settings-form">
        {/* Section 1: Modes de fonctionnement */}
        <div className="settings-card">
          <div className="settings-card-header">
            <h3>⚙️ Mode de réponse IA</h3>
            <p className="text-muted">
              Définissez le niveau d'autonomie accordé à l'assistant Community Manager pour ce workspace.
            </p>
          </div>

          <div className="mode-selection-grid">
            {/* Mode 1: Manuel */}
            <div
              className={`mode-card ${settings.mode === 'MANUAL' ? 'selected' : ''}`}
              onClick={() => setSettings({ ...settings, mode: 'MANUAL' as AICMMode })}
            >
              <div className="mode-radio">
                <input
                  type="radio"
                  name="mode"
                  checked={settings.mode === 'MANUAL'}
                  onChange={() => setSettings({ ...settings, mode: 'MANUAL' as AICMMode })}
                />
              </div>
              <div className="mode-content">
                <div className="mode-title">Mode 1 : Manuel</div>
                <p className="mode-desc">
                  L'IA analyse les messages et propose des suggestions. Aucun message n'est préparé ni envoyé sans action explicite d'un humain.
                </p>
              </div>
            </div>

            {/* Mode 2: Validation obligatoire */}
            <div
              className={`mode-card ${settings.mode === 'APPROVAL_REQUIRED' ? 'selected' : ''}`}
              onClick={() => setSettings({ ...settings, mode: 'APPROVAL_REQUIRED' as AICMMode })}
            >
              <div className="mode-radio">
                <input
                  type="radio"
                  name="mode"
                  checked={settings.mode === 'APPROVAL_REQUIRED'}
                  onChange={() => setSettings({ ...settings, mode: 'APPROVAL_REQUIRED' as AICMMode })}
                />
              </div>
              <div className="mode-content">
                <div className="mode-title">
                  Mode 2 : Validation obligatoire <span className="recommended-badge">Recommandé (Par défaut)</span>
                </div>
                <p className="mode-desc">
                  L'IA prépare proactivement les brouillons de réponse. Un membre de l'équipe doit les examiner et les approuver avant envoi sur les réseaux.
                </p>
              </div>
            </div>

            {/* Mode 3: Automatique */}
            <div
              className={`mode-card ${settings.mode === 'AUTOMATIC' ? 'selected' : ''}`}
              onClick={() => setSettings({ ...settings, mode: 'AUTOMATIC' as AICMMode })}
            >
              <div className="mode-radio">
                <input
                  type="radio"
                  name="mode"
                  checked={settings.mode === 'AUTOMATIC'}
                  onChange={() => setSettings({ ...settings, mode: 'AUTOMATIC' as AICMMode })}
                />
              </div>
              <div className="mode-content">
                <div className="mode-title">Mode 3 : Automatique (Supervisé)</div>
                <p className="mode-desc">
                  L'IA peut publier automatiquement UNIQUEMENT les réponses simples et sûres répondant aux critères stricts ci-dessous.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Réseaux Sociaux & Langues */}
        <div className="settings-card">
          <div className="settings-card-header">
            <h3>🌐 Réseaux Sociaux & Langues autorisées</h3>
          </div>

          <div className="settings-row">
            <div className="setting-block">
              <label className="block-title">Plateformes activées</label>
              <div className="checkboxes-row">
                {[
                  { id: 'facebook', label: 'Facebook Page' },
                  { id: 'instagram', label: 'Instagram' },
                  { id: 'linkedin', label: 'LinkedIn' },
                ].map((p) => (
                  <label key={p.id} className="custom-checkbox">
                    <input
                      type="checkbox"
                      checked={settings.enabled_platforms.includes(p.id)}
                      onChange={() => handlePlatformToggle(p.id)}
                    />
                    <span>{p.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="setting-block">
              <label className="block-title">Langues acceptées pour les réponses IA</label>
              <input
                type="text"
                className="form-control"
                value={(settings.allowed_languages || []).join(', ')}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    allowed_languages: e.target.value.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean),
                  })
                }
                placeholder="fr, en"
              />
              <span className="field-hint">Codes ISO séparés par une virgule (ex: fr, en).</span>
            </div>
          </div>
        </div>

        {/* Section 3: Règles de sécurité et Garde-fous (Strict Safety) */}
        <div className="settings-card card-security">
          <div className="settings-card-header">
            <h3>🛡️ Garde-fous & Sécurité Stricte</h3>
            <span className="security-tag">Sécurité Obligatoire</span>
          </div>

          <div className="confidence-slider-group">
            <div className="slider-header">
              <label>Seuil de confiance minimal pour l'automatisation</label>
              <span className="confidence-value">{Math.round(settings.min_confidence_score * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.70"
              max="0.99"
              step="0.01"
              value={settings.min_confidence_score}
              onChange={(e) => setSettings({ ...settings, min_confidence_score: parseFloat(e.target.value) })}
              className="range-slider"
            />
            <p className="field-hint">
              Si le score de confiance calculé par l'IA est inférieur à ce seuil, aucune réponse automatique ne sera envoyée.
            </p>
          </div>

          <div className="intents-settings-grid">
            <div className="intents-allowed-col">
              <label className="block-title">✅ Intentions éligibles à l'envoi auto (Mode 3)</label>
              <div className="checkboxes-column">
                {[
                  { id: 'compliment', label: 'Compliments et remerciements' },
                  { id: 'question', label: 'Questions générales (avec FAQ existante)' },
                  { id: 'support_request', label: 'Demande de support basique' },
                  { id: 'price_inquiry', label: 'Demande de prix de catalogue vérifié' },
                  { id: 'delivery_inquiry', label: 'Demande de délais de livraison standard' },
                ].map((it) => (
                  <label key={it.id} className="custom-checkbox">
                    <input
                      type="checkbox"
                      checked={settings.auto_reply_intents.includes(it.id)}
                      onChange={() => handleIntentToggle(it.id)}
                    />
                    <span>{it.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="intents-blocked-col">
              <label className="block-title text-danger">⛔ Catégories strictement INTERDITES d'envoi auto</label>
              <ul className="blocked-categories-list">
                <li>🚫 <strong>Réclamations & Insatisfaction</strong> (complaint)</li>
                <li>🚫 <strong>Demandes de remboursement</strong> (refund)</li>
                <li>🚫 <strong>Menaces, insultes ou bad buzz</strong> (threat)</li>
                <li>🚫 <strong>Questions juridiques ou litiges</strong> (legal)</li>
                <li>🚫 <strong>Problèmes de paiement ou bancaires</strong> (payment_issue)</li>
                <li>🚫 <strong>Faits absents de la base de connaissances</strong> (missing info)</li>
              </ul>
              <p className="blocked-explanation">
                Ces interactions sont systématiquement bloquées et nécessitent une intervention humaine.
              </p>
            </div>
          </div>

          <div className="working-hours-toggle">
            <label className="custom-switch">
              <input
                type="checkbox"
                checked={settings.working_hours_only}
                onChange={(e) => setSettings({ ...settings, working_hours_only: e.target.checked })}
              />
              <span className="switch-slider" />
              <span className="switch-label">Restreindre l'automatisation aux heures de bureau uniquement</span>
            </label>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="aicm-settings-footer">
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
            {saving ? 'Enregistrement...' : '💾 Enregistrer les Paramètres d’Automatisation'}
          </button>
        </div>
      </form>
    </div>
  )
}
