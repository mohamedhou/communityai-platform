import { useState } from 'react'

interface ReplyBoxProps {
  onSuggestReply: (tone: string, instructions?: string) => Promise<string | undefined>
  onSendReply: (content: string) => Promise<void>
  isSuggesting: boolean
  isSending: boolean
  isResolved: boolean
}

export function ReplyBox({
  onSuggestReply,
  onSendReply,
  isSuggesting,
  isSending,
  isResolved,
}: ReplyBoxProps) {
  const [content, setContent] = useState('')
  const [selectedTone, setSelectedTone] = useState('PROFESSIONAL')
  const [customInstructions, setCustomInstructions] = useState('')
  const [showOptions, setShowOptions] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleSuggest = async () => {
    try {
      setError(null)
      const suggestion = await onSuggestReply(selectedTone, customInstructions || undefined)
      if (suggestion) {
        setContent(suggestion)
        setSuccess('Suggestion IA générée ! Vous pouvez la modifier avant envoi.')
      }
    } catch (err: any) {
      setError(err.message || 'Échec de la suggestion IA')
    }
  }

  const handleSend = async () => {
    if (!content.trim()) {
      setError('Veuillez saisir une réponse avant d’envoyer.')
      return
    }

    try {
      setError(null)
      await onSendReply(content.trim())
      setContent('')
      setSuccess('Réponse envoyée avec succès et interaction résolue !')
    } catch (err: any) {
      setError(err.message || "Échec de l'envoi de la réponse")
    }
  }

  return (
    <div className="reply-box-card">
      <div className="reply-box-header">
        <h4 className="reply-box-title">✍️ Répondre à cette interaction</h4>
        <button
          type="button"
          className="reply-options-toggle"
          onClick={() => setShowOptions(!showOptions)}
        >
          {showOptions ? 'Masquer les options IA' : '⚙️ Options IA'}
        </button>
      </div>

      {showOptions && (
        <div className="reply-ai-options">
          <div className="reply-ai-option-row">
            <label className="reply-option-label">Ton souhaité :</label>
            <select
              value={selectedTone}
              onChange={(e) => setSelectedTone(e.target.value)}
              className="reply-tone-select"
            >
              <option value="PROFESSIONAL">Professionnel & Posé</option>
              <option value="FRIENDLY">Chaleureux & Amical</option>
              <option value="FORMAL">Formel & Précis</option>
              <option value="CASUAL">Décontracté</option>
            </select>
          </div>
          <div className="reply-ai-option-row">
            <label className="reply-option-label">Consigne spécifique (optionnel) :</label>
            <input
              type="text"
              placeholder="Ex: Proposer un appel téléphonique, s'excuser pour le retard..."
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              className="reply-instruction-input"
            />
          </div>
        </div>
      )}

      {error && <div className="reply-alert reply-alert-error">{error}</div>}
      {success && <div className="reply-alert reply-alert-success">{success}</div>}

      <div className="reply-textarea-wrapper">
        <textarea
          rows={4}
          placeholder="Rédigez votre réponse ici ou utilisez le bouton d'assistance IA ci-dessous..."
          value={content}
          onChange={(e) => {
            setContent(e.target.value)
            setError(null)
            setSuccess(null)
          }}
          className="reply-textarea"
          disabled={isSending}
        />
      </div>

      <div className="reply-actions-row">
        <button
          type="button"
          className="btn btn-ai-suggest"
          onClick={handleSuggest}
          disabled={isSuggesting || isSending}
        >
          {isSuggesting ? (
            <>
              <span className="spinner-small" /> Génération IA en cours...
            </>
          ) : (
            '✨ Suggérer une réponse (IA)'
          )}
        </button>

        <div className="reply-submit-group">
          {content && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setContent('')}
              disabled={isSending}
            >
              Effacer
            </button>
          )}
          <button
            type="button"
            className="btn btn-primary btn-send-reply"
            onClick={handleSend}
            disabled={isSending || !content.trim()}
          >
            {isSending ? (
              <>
                <span className="spinner-small" /> Envoi en cours...
              </>
            ) : isResolved ? (
              '🚀 Envoyer une nouvelle réponse'
            ) : (
              '🚀 Envoyer & Marquer comme traité'
            )}
          </button>
        </div>
      </div>
      <p className="reply-disclaimer">
        🛡️ <strong>Validation humaine obligatoire :</strong> L’IA suggère uniquement un brouillon de réponse. Aucun message n’est expédié sans votre action manuelle.
      </p>
    </div>
  )
}
