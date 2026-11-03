import { useEffect, useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import type { InboxMessage } from '../types/inbox'
import { ReplyBox } from './ReplyBox'
import { SentimentBadge } from './SentimentBadge'
import {
  analyzeInboxMessage,
  approveAICMDraft,
  escalateAICMMessage,
  generateAICMReply,
  getAICMMessageContext,
  listAICMDrafts,
} from '../../ai-cm/services/aiCmApi'
import type { AIReplyDraft } from '../../ai-cm/types'

interface InboxDetailProps {
  message: InboxMessage | null
  onToggleRead: (messageId: number, currentRead: boolean) => Promise<any>
  onToggleResolved: (messageId: number, currentResolved: boolean) => Promise<any>
  onSuggestReply: (tone: string, instructions?: string) => Promise<string | undefined>
  onSendReply: (content: string) => Promise<any>
  isSuggesting: boolean
  isSending: boolean
}

export function InboxDetail({
  message,
  onToggleRead,
  onToggleResolved,
  onSuggestReply,
  onSendReply,
  isSuggesting,
  isSending,
}: InboxDetailProps) {
  const { accessToken } = useAuth()
  const [activeDraft, setActiveDraft] = useState<AIReplyDraft | null>(null)
  const [loadingDraft, setLoadingDraft] = useState<boolean>(false)
  const [analyzing, setAnalyzing] = useState<boolean>(false)
  const [showContext, setShowContext] = useState<boolean>(false)
  const [contextData, setContextData] = useState<any | null>(null)

  // Escalation Modal
  const [showEscalateModal, setShowEscalateModal] = useState<boolean>(false)
  const [escalationNote, setEscalationNote] = useState<string>('')
  const [isEscalating, setIsEscalating] = useState<boolean>(false)

  // Pre-fill text in reply box
  const [prefilledReply, setPrefilledReply] = useState<string | null>(null)

  // Load existing draft for selected message
  const messageId = message?.id
  useEffect(() => {
    setActiveDraft(null)
    setShowContext(false)
    setContextData(null)
    setPrefilledReply(null)

    if (!messageId || !accessToken) return

    const loadDraft = async () => {
      try {
        const drafts = await listAICMDrafts(accessToken)
        const matched = drafts.find((d) => d.inbox_message_id === messageId)
        if (matched) {
          setActiveDraft(matched)
        }
      } catch {
        // silent
      }
    }
    loadDraft()
  }, [messageId, accessToken])

  if (!message) {
    return (
      <div className="inbox-detail-empty">
        <div className="inbox-detail-empty-icon">👈</div>
        <h3>Sélectionnez une interaction</h3>
        <p>Cliquez sur un message ou commentaire dans la liste de gauche pour l'analyser et y répondre.</p>
      </div>
    )
  }

  const formatFullDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('fr-FR', {
        dateStyle: 'full',
        timeStyle: 'short',
      })
    } catch {
      return dateStr
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'COMMENT':
        return 'Commentaire'
      case 'MESSAGE':
        return 'Message privé'
      case 'MENTION':
        return 'Mention publique'
      default:
        return type
    }
  }

  const platform = message.social_account?.platform || message.social_account?.provider || 'social'
  const accountName = message.social_account?.account_name || 'Compte Social'

  // Trigger on-demand AI analysis
  const handleAnalyze = async () => {
    if (!accessToken) return
    setAnalyzing(true)
    try {
      const res = await analyzeInboxMessage(accessToken, message.id)
      message.intent = res.intent
      message.urgency = res.urgency
      message.ai_analysis = res as any
    } catch {
      // silent
    } finally {
      setAnalyzing(false)
    }
  }

  // Trigger AI grounded generation
  const handleGenerateReply = async () => {
    if (!accessToken) return
    setLoadingDraft(true)
    try {
      const draft = await generateAICMReply(accessToken, message.id)
      setActiveDraft(draft)
    } catch (err: any) {
      alert(err.message || 'Erreur lors de la génération.')
    } finally {
      setLoadingDraft(false)
    }
  }

  // Approve and send draft
  const handleApproveDraft = async () => {
    if (!accessToken || !activeDraft) return
    try {
      const updated = await approveAICMDraft(accessToken, activeDraft.id, true, undefined, true)
      setActiveDraft(updated)
      message.is_resolved = true
      message.is_read = true
    } catch (err: any) {
      alert(err.message || 'Erreur lors de l’envoi.')
    }
  }

  // Reject draft
  const handleRejectDraft = async () => {
    if (!accessToken || !activeDraft) return
    try {
      const updated = await approveAICMDraft(accessToken, activeDraft.id, false)
      setActiveDraft(updated)
    } catch (err: any) {
      alert(err.message || 'Erreur lors du rejet.')
    }
  }

  // Load business context
  const handleToggleContext = async () => {
    if (!showContext && !contextData && accessToken) {
      try {
        const data = await getAICMMessageContext(accessToken, message.id)
        setContextData(data)
      } catch {
        // silent
      }
    }
    setShowContext(!showContext)
  }

  // Handle Escalation
  const handleEscalateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!accessToken || !escalationNote.trim()) return
    setIsEscalating(true)
    try {
      await escalateAICMMessage(accessToken, message.id, escalationNote.trim())
      message.is_escalated = true
      message.escalation_note = escalationNote.trim()
      setShowEscalateModal(false)
      setEscalationNote('')
    } catch (err: any) {
      alert(err.message || 'Erreur lors de l’escalade.')
    } finally {
      setIsEscalating(false)
    }
  }

  const aiAnalysis = message.ai_analysis

  return (
    <div className="inbox-detail-container">
      {/* Top action header */}
      <div className="inbox-detail-header">
        <div className="inbox-detail-sender-info">
          <div className="inbox-detail-avatar">
            {message.sender_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="inbox-detail-sender-name">{message.sender_name}</h3>
            <p className="inbox-detail-account-sub">
              Via <span className="platform-highlight">{platform.toUpperCase()}</span> ({accountName})
              • <span className="type-highlight">{getTypeLabel(message.type)}</span>
            </p>
          </div>
        </div>

        <div className="inbox-detail-quick-actions">
          <button
            type="button"
            className={`btn-action ${message.is_read ? 'btn-action-active' : ''}`}
            onClick={() => onToggleRead(message.id, message.is_read)}
            title={message.is_read ? 'Marquer comme non lu' : 'Marquer comme lu'}
          >
            {message.is_read ? '📖 Lu' : '📬 Marquer lu'}
          </button>

          <button
            type="button"
            className={`btn-action ${message.is_resolved ? 'btn-action-resolved' : ''}`}
            onClick={() => onToggleResolved(message.id, message.is_resolved)}
            title={message.is_resolved ? 'Rouvrir l’interaction' : 'Marquer comme traité'}
          >
            {message.is_resolved ? '✅ Traité' : '⏳ Marquer traité'}
          </button>

          <button
            type="button"
            className={`btn-action btn-escalate ${message.is_escalated ? 'escalated-active' : ''}`}
            onClick={() => setShowEscalateModal(true)}
            title="Escalader à un responsable"
          >
            {message.is_escalated ? '🚨 Escaladé' : '👤 Escalader'}
          </button>
        </div>
      </div>

      {/* Meta details strip */}
      <div className="inbox-detail-meta-bar">
        <div className="meta-bar-item">
          <span className="meta-bar-label">Sentiment :</span>
          <SentimentBadge
            sentiment={message.sentiment}
            score={message.sentiment_score}
            showScore={true}
          />
        </div>

        {message.intent && (
          <div className="meta-bar-item">
            <span className="meta-bar-label">Intention :</span>
            <span className="aicm-tag intent-tag">{message.intent}</span>
          </div>
        )}

        {message.urgency && (
          <div className="meta-bar-item">
            <span className="meta-bar-label">Urgence :</span>
            <span className={`aicm-tag urgency-tag ${message.urgency}`}>
              {message.urgency === 'critical' ? '🚨 Critique' : message.urgency === 'high' ? '🔥 Élevée' : 'Normale'}
            </span>
          </div>
        )}

        <div className="meta-bar-item">
          <span className="meta-bar-label">Reçu le :</span>
          <span className="meta-bar-value">{formatFullDate(message.created_at)}</span>
        </div>

        {message.replied_at && (
          <div className="meta-bar-item replied-status">
            <span className="meta-bar-label">Répondu le :</span>
            <span className="meta-bar-value">{formatFullDate(message.replied_at)}</span>
          </div>
        )}
      </div>

      {/* Escalation Alert if flagged */}
      {message.is_escalated && (
        <div className="aicm-escalation-alert">
          <span className="alert-icon">🚨</span>
          <div>
            <strong>Interaction escaladée à un responsable</strong>
            {message.escalation_note && <p className="escalation-note">{message.escalation_note}</p>}
          </div>
        </div>
      )}

      {/* Message Content Card */}
      <div className="inbox-detail-message-card">
        <div className="message-card-header">
          <span className="message-type-badge">{getTypeLabel(message.type)}</span>
          <span className="message-origin-id">ID Externe: {message.external_id}</span>
        </div>
        <div className="message-card-body">
          <p>{message.content}</p>
        </div>
      </div>

      {/* AI Community Manager Analysis Card */}
      <div className="aicm-analysis-card">
        <div className="analysis-card-header">
          <div className="analysis-title">
            <span>🔍 Analyse Sémantique IA</span>
            {aiAnalysis?.confidence && (
              <span className="confidence-pill">
                Fiabilité : {Math.round(aiAnalysis.confidence * 100)}%
              </span>
            )}
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-xs"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? 'Analyse...' : '🔄 Rafraîchir l’analyse'}
          </button>
        </div>

        {aiAnalysis ? (
          <div className="analysis-card-body">
            <div className="analysis-row">
              <span className="analysis-label">Besoin détecté :</span>
              <span className="analysis-val">{aiAnalysis.customer_need || 'Information générale'}</span>
            </div>
            {aiAnalysis.potential_risk && (
              <div className="analysis-row risk-row">
                <span className="analysis-label">Risque identifié :</span>
                <span className="analysis-val text-danger">{aiAnalysis.potential_risk}</span>
              </div>
            )}
            <div className="analysis-row">
              <span className="analysis-label">Motif & Justification :</span>
              <span className="analysis-val">{aiAnalysis.reason}</span>
            </div>
          </div>
        ) : (
          <p className="text-muted" style={{ margin: '8px 0 0' }}>
            Aucune analyse effectuée. Cliquez sur le bouton ci-dessus pour classifier l'intention et le sentiment.
          </p>
        )}
      </div>

      {/* AI Grounded Suggestion Panel */}
      <div className="aicm-draft-card">
        <div className="draft-card-header">
          <div className="draft-card-title">
            <span>🤖 Proposition de Réponse Vérifiée</span>
            {activeDraft && (
              <span className={`draft-status-badge status-${activeDraft.status.toLowerCase()}`}>
                {activeDraft.status === 'SENT'
                  ? 'Envoyée'
                  : activeDraft.status === 'APPROVED'
                  ? 'Approuvée'
                  : activeDraft.status === 'REJECTED'
                  ? 'Rejetée'
                  : 'Brouillon prêt'}
              </span>
            )}
          </div>

          <div className="draft-header-actions">
            <button
              type="button"
              className="btn btn-outline btn-xs"
              onClick={handleToggleContext}
            >
              {showContext ? 'Masquer le contexte ✕' : 'ℹ️ Contexte utilisé'}
            </button>
            <button
              type="button"
              className="btn btn-primary btn-xs"
              onClick={handleGenerateReply}
              disabled={loadingDraft}
            >
              {loadingDraft ? 'Génération...' : activeDraft ? '🔄 Régénérer' : '✨ Générer proposition'}
            </button>
          </div>
        </div>

        {/* Collapsible Context Drawer */}
        {showContext && contextData && (
          <div className="aicm-context-drawer">
            <h4>🏢 Données Entreprise Utilisées par l'IA :</h4>
            <div className="context-item">
              <strong>Entreprise :</strong> {contextData.company_profile?.name} (
              {contextData.company_profile?.industry})
            </div>
            {contextData.relevant_products && contextData.relevant_products.length > 0 && (
              <div className="context-item">
                <strong>Produits correspondants :</strong>{' '}
                {contextData.relevant_products.map((p: any) => p.name).join(', ')}
              </div>
            )}
            {contextData.relevant_faqs && contextData.relevant_faqs.length > 0 && (
              <div className="context-item">
                <strong>FAQ citées :</strong>{' '}
                {contextData.relevant_faqs.map((f: any) => `"${f.question}"`).join(', ')}
              </div>
            )}
            <div className="context-item">
              <strong>Ton appliqué :</strong> {contextData.editorial_guidelines?.tone}
            </div>
          </div>
        )}

        {/* Draft Body */}
        {activeDraft ? (
          <div className="draft-card-body">
            <div className="draft-bubble">
              <p>{activeDraft.reply_text}</p>
            </div>

            {/* Sources Citations */}
            {activeDraft.sources_used && activeDraft.sources_used.length > 0 && (
              <div className="draft-sources-row">
                <span className="sources-label">Sources officielles :</span>
                {activeDraft.sources_used.map((s, idx) => (
                  <span key={idx} className="source-tag">
                    📌 {s}
                  </span>
                ))}
              </div>
            )}

            {/* Human escalation justification if flagged */}
            {activeDraft.requires_human && (
              <div className="draft-warning-row">
                ⚠️ <strong>Validation humaine obligatoire :</strong>{' '}
                {activeDraft.escalation_reason || 'Règle de sécurité ou sensibilité détectée.'}
              </div>
            )}

            {/* Draft Actions */}
            {activeDraft.status === 'SUGGESTED' && (
              <div className="draft-actions-bar">
                <button
                  type="button"
                  className="btn btn-success btn-sm"
                  onClick={handleApproveDraft}
                >
                  ✅ Approuver &amp; Envoyer
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setPrefilledReply(activeDraft.reply_text)}
                >
                  ✏️ Modifier avant envoi
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm text-danger"
                  onClick={handleRejectDraft}
                >
                  ✕ Rejeter
                </button>
              </div>
            )}
          </div>
        ) : (
          <p className="text-muted draft-placeholder">
            Générez une réponse avec l'IA grounded sur les informations de votre entreprise en cliquant sur "Générer proposition".
          </p>
        )}
      </div>

      {/* Manual & Edited Reply Box */}
      <ReplyBox
        onSuggestReply={onSuggestReply}
        onSendReply={onSendReply}
        isSuggesting={isSuggesting}
        isSending={isSending}
        isResolved={message.is_resolved}
        initialContent={prefilledReply}
      />

      {/* Escalation Modal */}
      {showEscalateModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <h3>🚨 Escalader cette interaction</h3>
              <button
                type="button"
                className="btn-close"
                onClick={() => setShowEscalateModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleEscalateSubmit}>
              <div className="modal-body">
                <p className="text-muted">
                  Transférez cette conversation délicate au responsable du Community Management ou au service client.
                </p>
                <div className="form-group">
                  <label>Justification de l'escalade *</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={escalationNote}
                    onChange={(e) => setEscalationNote(e.target.value)}
                    placeholder="Ex: Le client menace de déposer plainte pour retard de livraison..."
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowEscalateModal(false)}
                >
                  Annuler
                </button>
                <button type="submit" className="btn btn-danger" disabled={isEscalating}>
                  {isEscalating ? 'Escalade...' : 'Transférer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
