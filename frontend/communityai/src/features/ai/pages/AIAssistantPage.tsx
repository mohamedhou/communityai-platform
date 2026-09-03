import { useAIAssistant } from '../hooks/useAIAssistant'
import { AIActionSelector } from '../components/AIActionSelector'
import { AIOptions } from '../components/AIOptions'
import { AIResult } from '../components/AIResult'
import { AIHistory } from '../components/AIHistory'

export function AIAssistantPage() {
  const {
    action,
    setAction,
    prompt,
    setPrompt,
    content,
    setContent,
    platform,
    setPlatform,
    tone,
    setTone,
    audience,
    setAudience,
    objective,
    setObjective,
    editorialContext,
    setEditorialContext,
    showEditorialContext,
    setShowEditorialContext,
    result,
    error,
    copied,
    isLoading,
    history,
    generate,
    handleCopy,
    handleUseInPostEditor,
    handleSelectHistoryItem,
    handleClearHistory,
  } = useAIAssistant()

  const isPromptBased = action === 'GENERATE' || action === 'IDEATE'

  const buttonLabel = (() => {
    switch (action) {
      case 'GENERATE':
        return '✨ Generate Publication'
      case 'REWRITE':
        return '🔄 Rewrite Content'
      case 'IMPROVE':
        return '⚡ Improve Copy'
      case 'SHORTEN':
        return '✂️ Shorten Copy'
      case 'EXPAND':
        return '📖 Expand Text'
      case 'CHANGE_TONE':
        return '🎭 Transform Tone'
      case 'ADAPT_PLATFORM':
        return '🌐 Adapt for Platform'
      case 'IDEATE':
        return '💡 Brainstorm Ideas'
      default:
        return '✨ Generate'
    }
  })()

  return (
    <main className="page-shell">
      <div className="ai-page-container">
        {/* Page Title & Intro */}
        <div className="ai-page-header">
          <div className="ai-header-badge">AI ASSISTANT</div>
          <h1>AI Content Studio</h1>
          <p className="page-subtitle">
            Generate, refine, and adapt social publications for Meta and LinkedIn with AI.
          </p>
        </div>

        {/* Action Tabs */}
        <AIActionSelector
          currentAction={action}
          onSelectAction={setAction}
          disabled={isLoading}
        />

        {/* Workspace: Left (Form & Options) / Right (Result & Actions) */}
        <div className="ai-workspace-grid">
          {/* Left Column: Inputs & Options */}
          <div className="ai-input-card">
            <h3 className="ai-section-title">
              {isPromptBased ? '1. Topic or Instructions' : '1. Original Publication Content'}
            </h3>

            {isPromptBased ? (
              <div className="ai-field-group">
                <label htmlFor="ai-prompt-input" className="ai-field-label">
                  {action === 'IDEATE'
                    ? 'What topic, theme, or industry should we brainstorm around?'
                    : 'What do you want to publish about?'}
                </label>
                <textarea
                  id="ai-prompt-input"
                  rows={5}
                  disabled={isLoading}
                  placeholder={
                    action === 'IDEATE'
                      ? 'e.g. B2B SaaS marketing tips, community building strategies, product launch teasers...'
                      : 'e.g. Announce our new sustainable product line with 20% off for early birds this weekend...'
                  }
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="ai-textarea-input"
                />
              </div>
            ) : (
              <div className="ai-field-group">
                <label htmlFor="ai-content-input" className="ai-field-label">
                  Text to {action.toLowerCase().replace('_', ' ')}
                </label>
                <textarea
                  id="ai-content-input"
                  rows={6}
                  disabled={isLoading}
                  placeholder="Paste or type your draft text here..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="ai-textarea-input"
                />
              </div>
            )}

            <h3 className="ai-section-title" style={{ marginTop: '20px' }}>
              2. Target Options & Tone
            </h3>

            <AIOptions
              action={action}
              platform={platform}
              onPlatformChange={setPlatform}
              tone={tone}
              onToneChange={setTone}
              audience={audience}
              onAudienceChange={setAudience}
              objective={objective}
              onObjectiveChange={setObjective}
              editorialContext={editorialContext}
              onEditorialContextChange={setEditorialContext}
              showEditorialContext={showEditorialContext}
              onToggleEditorialContext={() => setShowEditorialContext((p) => !p)}
              disabled={isLoading}
            />

            {/* Error Display */}
            {error && (
              <div className="ai-error-banner" role="alert">
                <span>⚠️ {error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="button"
              disabled={isLoading}
              onClick={() => generate()}
              className="ai-generate-submit-btn"
            >
              {isLoading ? '⏳ Generating...' : buttonLabel}
            </button>
          </div>

          {/* Right Column: AI Result Preview */}
          <div className="ai-result-column">
            <h3 className="ai-section-title">3. AI Generated Output</h3>
            <AIResult
              result={result}
              isLoading={isLoading}
              copied={copied}
              onCopy={handleCopy}
              onUseInPostEditor={handleUseInPostEditor}
              onRegenerate={() => generate()}
            />
          </div>
        </div>

        {/* Recent History Section */}
        <AIHistory
          history={history}
          onSelect={handleSelectHistoryItem}
          onClear={handleClearHistory}
          onUseInEditor={handleUseInPostEditor}
        />
      </div>
    </main>
  )
}
