import type { AIAction, AIPlatform, AITone } from '../types/ai'

interface AIOptionsProps {
  action: AIAction
  platform: AIPlatform | ''
  onPlatformChange: (p: AIPlatform | '') => void
  tone: AITone
  onToneChange: (t: AITone) => void
  audience: string
  onAudienceChange: (a: string) => void
  objective: string
  onObjectiveChange: (o: string) => void
  editorialContext: string
  onEditorialContextChange: (c: string) => void
  showEditorialContext: boolean
  onToggleEditorialContext: () => void
  language?: string
  onLanguageChange?: (lang: string) => void
  length?: 'short' | 'medium' | 'long' | ''
  onLengthChange?: (len: 'short' | 'medium' | 'long' | '') => void
  includeHashtags?: boolean
  onIncludeHashtagsChange?: (val: boolean) => void
  includeCta?: boolean
  onIncludeCtaChange?: (val: boolean) => void
  disabled?: boolean
}

const TONES: { key: AITone; label: string }[] = [
  { key: 'PROFESSIONAL', label: '💼 Professionnel' },
  { key: 'FRIENDLY', label: '🤝 Amical & Chaleureux' },
  { key: 'HUMOROUS', label: '🎭 Humoristique & Décalé' },
  { key: 'PROMOTIONAL', label: '🔥 Commercial & Promotionnel' },
  { key: 'CASUAL', label: '☕ Décontracté' },
  { key: 'FORMAL', label: '🏛️ Formel' },
  { key: 'TECHNICAL', label: '⚙️ Technique' },
]

const PLATFORMS: { key: AIPlatform | ''; label: string }[] = [
  { key: 'LINKEDIN', label: 'LinkedIn' },
  { key: 'INSTAGRAM', label: 'Instagram' },
  { key: 'FACEBOOK', label: 'Facebook' },
  { key: '', label: 'Général / Multi-réseaux' },
]

const LANGUAGES: { key: string; label: string }[] = [
  { key: 'fr', label: '🇫🇷 Français' },
  { key: 'en', label: '🇬🇧 Anglais' },
  { key: 'es', label: '🇪🇸 Espagnol' },
  { key: 'de', label: '🇩🇪 Allemand' },
]

const LENGTHS: { key: 'short' | 'medium' | 'long' | ''; label: string }[] = [
  { key: '', label: 'Automatique' },
  { key: 'short', label: 'Court (1-3 phrases)' },
  { key: 'medium', label: 'Moyen (1-2 paragraphes)' },
  { key: 'long', label: 'Long (détaillé & structuré)' },
]

export function AIOptions({
  action,
  platform,
  onPlatformChange,
  tone,
  onToneChange,
  audience,
  onAudienceChange,
  objective,
  onObjectiveChange,
  editorialContext,
  onEditorialContextChange,
  showEditorialContext,
  onToggleEditorialContext,
  language = 'fr',
  onLanguageChange,
  length = '',
  onLengthChange,
  includeHashtags = true,
  onIncludeHashtagsChange,
  includeCta = true,
  onIncludeCtaChange,
  disabled = false,
}: AIOptionsProps) {
  const showAudienceObjective = action === 'GENERATE' || action === 'IDEATE'
  const isPlatformRequired = action === 'ADAPT_PLATFORM'
  const isToneRequired = action === 'CHANGE_TONE'

  return (
    <div className="ai-options-container">
      <div className="ai-options-row">
        {/* Platform Selector */}
        <div className="ai-option-field">
          <label htmlFor="ai-platform-select" className="ai-field-label">
            Réseau social {isPlatformRequired && <span className="required-star">*</span>}
          </label>
          <select
            id="ai-platform-select"
            disabled={disabled}
            value={platform}
            onChange={(e) => onPlatformChange(e.target.value as AIPlatform | '')}
            className="ai-select-input"
          >
            {PLATFORMS.map((p) => (
              <option key={p.key} value={p.key}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {/* Tone Selector */}
        <div className="ai-option-field">
          <label htmlFor="ai-tone-select" className="ai-field-label">
            Ton de voix {isToneRequired && <span className="required-star">*</span>}
          </label>
          <select
            id="ai-tone-select"
            disabled={disabled}
            value={tone}
            onChange={(e) => onToneChange(e.target.value as AITone)}
            className="ai-select-input"
          >
            {TONES.map((t) => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="ai-options-row">
        {/* Language Selector */}
        {onLanguageChange && (
          <div className="ai-option-field">
            <label htmlFor="ai-language-select" className="ai-field-label">
              Langue
            </label>
            <select
              id="ai-language-select"
              disabled={disabled}
              value={language}
              onChange={(e) => onLanguageChange(e.target.value)}
              className="ai-select-input"
            >
              {LANGUAGES.map((l) => (
                <option key={l.key} value={l.key}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Length Selector */}
        {onLengthChange && action !== 'SHORTEN' && action !== 'EXPAND' && (
          <div className="ai-option-field">
            <label htmlFor="ai-length-select" className="ai-field-label">
              Longueur souhaitée
            </label>
            <select
              id="ai-length-select"
              disabled={disabled}
              value={length}
              onChange={(e) => onLengthChange(e.target.value as any)}
              className="ai-select-input"
            >
              {LENGTHS.map((l) => (
                <option key={l.key} value={l.key}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Toggles for Hashtags and CTA */}
      {(onIncludeHashtagsChange || onIncludeCtaChange) && (
        <div className="ai-toggles-row" style={{ display: 'flex', gap: '20px', marginTop: '4px', flexWrap: 'wrap' }}>
          {onIncludeHashtagsChange && (
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.88rem' }}>
              <input
                type="checkbox"
                checked={includeHashtags}
                disabled={disabled}
                onChange={(e) => onIncludeHashtagsChange(e.target.checked)}
                style={{ accentColor: '#4f46e5', width: '16px', height: '16px' }}
              />
              Inclure des hashtags pertinents (#)
            </label>
          )}

          {onIncludeCtaChange && (
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.88rem' }}>
              <input
                type="checkbox"
                checked={includeCta}
                disabled={disabled}
                onChange={(e) => onIncludeCtaChange(e.target.checked)}
                style={{ accentColor: '#4f46e5', width: '16px', height: '16px' }}
              />
              Inclure un appel à l'action (CTA)
            </label>
          )}
        </div>
      )}

      {/* Optional Audience & Objective for Generate/Ideate */}
      {showAudienceObjective && (
        <div className="ai-options-row">
          <div className="ai-option-field">
            <label htmlFor="ai-audience-input" className="ai-field-label">
              Public cible <span className="optional-tag">(optionnel)</span>
            </label>
            <input
              id="ai-audience-input"
              type="text"
              disabled={disabled}
              placeholder="ex: Directeurs Marketing, Freelances, Étudiants..."
              value={audience}
              onChange={(e) => onAudienceChange(e.target.value)}
              className="ai-text-input"
            />
          </div>

          <div className="ai-option-field">
            <label htmlFor="ai-objective-input" className="ai-field-label">
              Objectif de la publication <span className="optional-tag">(optionnel)</span>
            </label>
            <input
              id="ai-objective-input"
              type="text"
              disabled={disabled}
              placeholder="ex: Engagement, Lancement produit, Inscriptions webinaire..."
              value={objective}
              onChange={(e) => onObjectiveChange(e.target.value)}
              className="ai-text-input"
            />
          </div>
        </div>
      )}

      {/* Editorial Guidelines Collapsible */}
      <div className="ai-editorial-wrapper">
        <button
          type="button"
          onClick={onToggleEditorialContext}
          className="ai-editorial-toggle"
        >
          <span>{showEditorialContext ? '▾' : '▸'} Charte éditoriale de la marque</span>
          {editorialContext.trim() && <span className="ai-badge-active">Active</span>}
        </button>

        {showEditorialContext && (
          <div className="ai-editorial-body">
            <textarea
              rows={3}
              disabled={disabled}
              placeholder="ex: Toujours bienveillant, éviter le jargon trop complexe, mettre en avant l'innovation et la transparence."
              value={editorialContext}
              onChange={(e) => onEditorialContextChange(e.target.value)}
              className="ai-textarea-input"
            />
            <span className="ai-field-hint">
              Ces consignes sont directement intégrées au modèle IA pour respecter l'identité de marque.
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
