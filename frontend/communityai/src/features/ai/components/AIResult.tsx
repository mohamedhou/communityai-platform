import type { AIResponse } from '../types/ai'

interface AIResultProps {
  result: AIResponse | null
  isLoading: boolean
  copied: boolean
  onCopy: (text?: string) => void
  onUseInPostEditor: (text?: string) => void
  onRegenerate: () => void
}

export function AIResult({
  result,
  isLoading,
  copied,
  onCopy,
  onUseInPostEditor,
  onRegenerate,
}: AIResultProps) {
  if (isLoading) {
    return (
      <div className="ai-result-card loading-state">
        <div className="ai-spinner" />
        <h4>Crafting your publication with AI...</h4>
        <p className="ai-subtext">Applying platform constraints, tone nuances, and editorial rules.</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="ai-result-card empty-state">
        <div className="ai-empty-icon">✨</div>
        <h4>Your AI-generated content will appear here</h4>
        <p className="ai-subtext">
          Select an action above, configure your options, and click Generate to get started.
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
            {charCount} chars • {wordCount} words
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
            title="Generate another version"
          >
            🔄 Regenerate
          </button>
          <button
            type="button"
            onClick={() => onCopy()}
            className={`ai-btn-secondary ${copied ? 'btn-copied' : ''}`}
          >
            {copied ? '✓ Copied!' : '📋 Copy'}
          </button>
        </div>
      </div>

      {/* Ideas list display or single content */}
      {result.ideas && result.ideas.length > 0 ? (
        <div className="ai-ideas-list">
          <h4 className="ai-ideas-title">💡 Generated Publication Ideas:</h4>
          {result.ideas.map((idea, idx) => (
            <div key={idx} className="ai-idea-item">
              <div className="ai-idea-text">{idea}</div>
              <div className="ai-idea-actions">
                <button
                  type="button"
                  onClick={() => onCopy(idea)}
                  className="ai-idea-btn"
                  title="Copy this idea"
                >
                  📋 Copy
                </button>
                <button
                  type="button"
                  onClick={() => onUseInPostEditor(idea)}
                  className="ai-idea-btn btn-primary-idea"
                  title="Open this idea in Post Editor"
                >
                  🚀 Use in Editor
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="ai-result-content">
          <pre className="ai-content-pre">{result.content}</pre>
        </div>
      )}

      {/* Main Bottom Action Bar */}
      <div className="ai-result-footer">
        <div className="ai-human-in-the-loop-note">
          <span>🛡️ Human in the loop: Review or edit your copy before scheduling.</span>
        </div>

        <button
          type="button"
          onClick={() => onUseInPostEditor()}
          className="ai-btn-primary-action"
        >
          🚀 Use in Post Editor
        </button>
      </div>
    </div>
  )
}
