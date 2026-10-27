import type { AIResponse } from '../types/ai'

interface AIResultProps {
  result: AIResponse | null
  isLoading: boolean
  copied: boolean
  onCopy: (text?: string) => void
  onUseInPostEditor: (text?: string) => void
  onRegenerate: () => void
  onContentChange?: (newContent: string) => void
}

export function AIResult({
  result,
  isLoading,
  copied,
  onCopy,
  onUseInPostEditor,
  onRegenerate,
  onContentChange,
}: AIResultProps) {
  if (isLoading) {
    return (
      <div className="ai-result-card loading-state">
        <div className="ai-spinner" />
        <h4>Génération de votre publication en cours...</h4>
        <p className="ai-subtext">Application du ton, du réseau social et des règles éditoriales avec Ollama.</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="ai-result-card empty-state">
        <div className="ai-empty-icon">✨</div>
        <h4>Votre contenu généré apparaîtra ici</h4>
        <p className="ai-subtext">
          Choisissez une action, configurez vos options et cliquez sur Générer pour commencer.
        </p>
      </div>
    )
  }

  const charCount = result.content.length
  const wordCount = result.content.trim().split(/\s+/).filter(Boolean).length

  return (
    <div className="ai-result-card ready-state">
      <div className="ai-result-header">
        <div className="ai-result-badges">
          <span className="ai-badge-action">{result.action}</span>
          <span className="ai-badge-stats">
            {charCount} caractères • {wordCount} mots
          </span>
          {result.usage?.total_tokens && (
            <span className="ai-badge-tokens">{result.usage.total_tokens} tokens</span>
          )}
        </div>

        <div className="ai-result-quick-actions">
          <button
            type="button"
            onClick={onRegenerate}
            className="ai-btn-secondary"
            title="Générer une autre version"
          >
            🔄 Régénérer
          </button>
          <button
            type="button"
            onClick={() => onCopy()}
            className={`ai-btn-secondary ${copied ? 'btn-copied' : ''}`}
          >
            {copied ? '✓ Copié !' : '📋 Copier'}
          </button>
        </div>
      </div>

      {/* Ideas list display or editable content */}
      {result.ideas && result.ideas.length > 0 ? (
        <div className="ai-ideas-list">
          <h4 className="ai-ideas-title">💡 Idées de publications générées :</h4>
          {result.ideas.map((idea, idx) => (
            <div key={idx} className="ai-idea-item">
              <div className="ai-idea-text">{idea}</div>
              <div className="ai-idea-actions">
                <button
                  type="button"
                  onClick={() => onCopy(idea)}
                  className="ai-idea-btn"
                  title="Copier cette idée"
                >
                  📋 Copier
                </button>
                <button
                  type="button"
                  onClick={() => onUseInPostEditor(idea)}
                  className="ai-idea-btn btn-primary-idea"
                  title="Utiliser cette idée pour rédiger un post"
                >
                  🚀 Utiliser
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="ai-result-content">
          <div style={{ marginBottom: '6px', fontSize: '0.85rem', color: '#64748b' }}>
            ✏️ Vous pouvez modifier directement le texte généré ci-dessous avant de l'enregistrer :
          </div>
          <textarea
            className="ai-textarea-input"
            rows={8}
            value={result.content}
            onChange={(e) => onContentChange?.(e.target.value)}
            style={{ width: '100%', fontFamily: 'inherit', fontSize: '0.95rem', lineHeight: '1.6' }}
          />
        </div>
      )}

      {/* Main Bottom Action Bar */}
      <div className="ai-result-footer">
        <div className="ai-human-in-the-loop-note">
          <span>🛡️ Contrôle humain : Vérifiez ou ajustez le texte avant publication.</span>
        </div>

        <button
          type="button"
          onClick={() => onUseInPostEditor()}
          className="ai-btn-primary-action"
        >
          💾 Enregistrer en brouillon (Éditeur)
        </button>
      </div>
    </div>
  )
}
