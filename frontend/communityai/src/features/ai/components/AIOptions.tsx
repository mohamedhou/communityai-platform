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
  disabled?: boolean
}

const TONES: { key: AITone; label: string }[] = [
  { key: 'PROFESSIONAL', label: '💼 Professional' },
  { key: 'CASUAL', label: '☕ Casual' },
  { key: 'FRIENDLY', label: '🤝 Friendly' },
  { key: 'FORMAL', label: '🏛️ Formal' },
  { key: 'PROMOTIONAL', label: '🔥 Promotional' },
  { key: 'TECHNICAL', label: '⚙️ Technical' },
]

const PLATFORMS: { key: AIPlatform | ''; label: string }[] = [
  { key: 'LINKEDIN', label: 'LinkedIn' },
  { key: 'INSTAGRAM', label: 'Instagram' },
  { key: 'FACEBOOK', label: 'Facebook' },
  { key: '', label: 'General / Multi-channel' },
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
            Platform {isPlatformRequired && <span className="required-star">*</span>}
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
            Tone {isToneRequired && <span className="required-star">*</span>}
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

      {/* Optional Audience & Objective for Generate/Ideate */}
      {showAudienceObjective && (
        <div className="ai-options-row">
          <div className="ai-option-field">
            <label htmlFor="ai-audience-input" className="ai-field-label">
              Target Audience <span className="optional-tag">(optional)</span>
            </label>
            <input
              id="ai-audience-input"
              type="text"
              disabled={disabled}
              placeholder="e.g. CMOs, Freelancers, Gen-Z creators"
              value={audience}
              onChange={(e) => onAudienceChange(e.target.value)}
              className="ai-text-input"
            />
          </div>

          <div className="ai-option-field">
            <label htmlFor="ai-objective-input" className="ai-field-label">
              Goal / Objective <span className="optional-tag">(optional)</span>
            </label>
            <input
              id="ai-objective-input"
              type="text"
              disabled={disabled}
              placeholder="e.g. Engagement, Product Launch, Event Signups"
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
          <span>{showEditorialContext ? '▾' : '▸'} Brand Editorial Guidelines</span>
          {editorialContext.trim() && <span className="ai-badge-active">Active</span>}
        </button>

        {showEditorialContext && (
          <div className="ai-editorial-body">
            <textarea
              rows={3}
              disabled={disabled}
              placeholder="e.g. Always professional, positive tone, avoid aggressive slang, highlight innovation and sustainability."
              value={editorialContext}
              onChange={(e) => onEditorialContextChange(e.target.value)}
              className="ai-textarea-input"
            />
            <span className="ai-field-hint">
              These guidelines are directly integrated into the prompt to respect your brand identity.
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
