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
    language,
    setLanguage,
    length,
    setLength,
    includeHashtags,
    setIncludeHashtags,
    includeCta,
    setIncludeCta,
    result,
    updateResultContent,
    error,
    copied,
    isLoading,
    providerStatus,
    isStatusLoading,
    refetchStatus,
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
        return '✨ Générer la publication'
      case 'REWRITE':
        return '🔄 Réécrire le contenu'
      case 'IMPROVE':
        return '⚡ Améliorer le texte'
      case 'SHORTEN':
        return '✂️ Raccourcir le texte'
      case 'EXPAND':
        return '📖 Développer le texte'
      case 'CHANGE_TONE':
        return '🎭 Transformer le ton'
      case 'ADAPT_PLATFORM':
        return '🌐 Adapter au réseau'
      case 'IDEATE':
        return '💡 Trouver des idées'
      default:
        return '✨ Générer'
    }
  })()

  return (
    <main className="page-shell">
      <div className="ai-page-container">
        {/* Page Title & Intro */}
        <div className="ai-page-header">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div className="ai-header-badge">AI ASSISTANT</div>
              <h1>AI Content Studio</h1>
              <p className="page-subtitle">
                Générez, affinez et adaptez vos publications pour les réseaux sociaux avec Ollama.
              </p>
            </div>
            {providerStatus && (
              <div className={`ai-provider-badge ${providerStatus.available ? 'online' : 'offline'}`}>
                <span className="ai-provider-pill-icon">{providerStatus.provider === 'ollama' ? '🦙' : '🤖'}</span>
                <span className="ai-provider-pill-name">
                  <strong>{providerStatus.provider.toUpperCase()}</strong> : {providerStatus.model}
                </span>
                <span className={`ai-provider-pill-dot ${providerStatus.available ? 'dot-online' : 'dot-offline'}`} />
                <span className="ai-provider-pill-status">
                  {providerStatus.available ? 'En ligne' : 'Indisponible'}
                </span>
                <button
                  type="button"
                  onClick={() => refetchStatus()}
                  className="ai-provider-pill-refresh"
                  title="Actualiser le statut"
                  disabled={isStatusLoading}
                >
                  🔄
                </button>
              </div>
            )}
          </div>

          {providerStatus && !providerStatus.available && (
            <div className="ai-provider-warning-banner" role="alert">
              <div className="ai-provider-warning-icon">⚠️</div>
              <div className="ai-provider-warning-content">
                <strong>Fournisseur IA ({providerStatus.provider}) indisponible</strong>
                <p>{providerStatus.error}</p>
                {providerStatus.provider === 'ollama' && (
                  <div className="ai-provider-warning-help">
                    <span>Pour lancer Ollama :</span>
                    <code>ollama serve</code>
                    <span>Pour installer le modèle :</span>
                    <code>ollama pull {providerStatus.model}</code>
                  </div>
                )}
              </div>
            </div>
          )}
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
              {isPromptBased ? '1. Sujet ou Consignes' : '1. Contenu original'}
            </h3>

            {isPromptBased ? (
              <div className="ai-field-group">
                <label htmlFor="ai-prompt-input" className="ai-field-label">
                  {action === 'IDEATE'
                    ? 'Sur quel sujet, thème ou secteur souhaitez-vous brainstormer ?'
                    : 'De quoi voulez-vous parler dans votre publication ?'}
                </label>
                <textarea
                  id="ai-prompt-input"
                  rows={5}
                  disabled={isLoading}
                  placeholder={
                    action === 'IDEATE'
                      ? 'ex: Astuces marketing B2B, stratégies d’engagement Instagram, teasers de lancement produit...'
                      : 'ex: Annonce de notre nouvelle offre avec -20% pour les premiers inscrits ce week-end...'
                  }
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="ai-textarea-input"
                />
              </div>
            ) : (
              <div className="ai-field-group">
                <label htmlFor="ai-content-input" className="ai-field-label">
                  Texte à {action.toLowerCase().replace('_', ' ')}
                </label>
                <textarea
                  id="ai-content-input"
                  rows={6}
                  disabled={isLoading}
                  placeholder="Collez ou saisissez votre brouillon ici..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="ai-textarea-input"
                />
              </div>
            )}

            <h3 className="ai-section-title" style={{ marginTop: '20px' }}>
              2. Paramètres & Tonalité
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
              language={language}
              onLanguageChange={setLanguage}
              length={length}
              onLengthChange={setLength}
              includeHashtags={includeHashtags}
              onIncludeHashtagsChange={setIncludeHashtags}
              includeCta={includeCta}
              onIncludeCtaChange={setIncludeCta}
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
              {isLoading ? '⏳ Génération en cours...' : buttonLabel}
            </button>
          </div>

          {/* Right Column: AI Result Preview */}
          <div className="ai-result-column">
            <h3 className="ai-section-title">3. Résultat IA</h3>
            <AIResult
              result={result}
              isLoading={isLoading}
              copied={copied}
              onCopy={handleCopy}
              onUseInPostEditor={handleUseInPostEditor}
              onRegenerate={() => generate()}
              onContentChange={updateResultContent}
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
