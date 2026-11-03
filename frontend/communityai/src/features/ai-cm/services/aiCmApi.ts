import { API_BASE_URL } from '../../../lib/env'
import type {
  AIAnalysisResult,
  AICMAuditLog,
  AICMDashboardMetrics,
  AICMSettings,
  AIReplyDraft,
  BusinessKnowledge,
  KnowledgeFAQ,
  KnowledgeProduct,
} from '../types'

const BK_BASE = `${API_BASE_URL}/api/v1/business-knowledge`
const AICM_BASE = `${API_BASE_URL}/api/v1/ai-cm`

function authHeaders(token: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }
}

async function handleResponse<T>(res: Response, defaultError: string): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: defaultError }))
    throw new Error(err.detail || defaultError)
  }
  if (res.status === 204) {
    return {} as T
  }
  return res.json()
}

// ==========================================
// Business Knowledge Base API
// ==========================================

export async function getBusinessKnowledge(token: string): Promise<BusinessKnowledge> {
  const res = await fetch(BK_BASE, { headers: authHeaders(token) })
  return handleResponse<BusinessKnowledge>(res, 'Impossible de charger la base de connaissances.')
}

export async function updateBusinessKnowledge(
  token: string,
  payload: Partial<BusinessKnowledge>,
): Promise<BusinessKnowledge> {
  const res = await fetch(BK_BASE, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  })
  return handleResponse<BusinessKnowledge>(res, 'Échec de la mise à jour de la base de connaissances.')
}

export async function seedDefaultKnowledge(token: string): Promise<BusinessKnowledge> {
  const res = await fetch(`${BK_BASE}/seed-default`, {
    method: 'POST',
    headers: authHeaders(token),
  })
  return handleResponse<BusinessKnowledge>(res, 'Impossible de pré-remplir les données métier.')
}

// Products
export async function listKnowledgeProducts(token: string): Promise<KnowledgeProduct[]> {
  const res = await fetch(`${BK_BASE}/products`, { headers: authHeaders(token) })
  return handleResponse<KnowledgeProduct[]>(res, 'Impossible de charger les produits.')
}

export async function createKnowledgeProduct(
  token: string,
  product: Omit<KnowledgeProduct, 'id' | 'workspace_id' | 'created_at' | 'updated_at'>,
): Promise<KnowledgeProduct> {
  const res = await fetch(`${BK_BASE}/products`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(product),
  })
  return handleResponse<KnowledgeProduct>(res, 'Impossible d’ajouter le produit.')
}

export async function updateKnowledgeProduct(
  token: string,
  productId: number,
  product: Partial<KnowledgeProduct>,
): Promise<KnowledgeProduct> {
  const res = await fetch(`${BK_BASE}/products/${productId}`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(product),
  })
  return handleResponse<KnowledgeProduct>(res, 'Impossible de modifier le produit.')
}

export async function deleteKnowledgeProduct(token: string, productId: number): Promise<void> {
  const res = await fetch(`${BK_BASE}/products/${productId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
  return handleResponse<void>(res, 'Impossible de supprimer le produit.')
}

// FAQs
export async function listKnowledgeFAQs(token: string, category?: string): Promise<KnowledgeFAQ[]> {
  const url = category ? `${BK_BASE}/faqs?category=${encodeURIComponent(category)}` : `${BK_BASE}/faqs`
  const res = await fetch(url, { headers: authHeaders(token) })
  return handleResponse<KnowledgeFAQ[]>(res, 'Impossible de charger les FAQs.')
}

export async function createKnowledgeFAQ(
  token: string,
  faq: Omit<KnowledgeFAQ, 'id' | 'workspace_id' | 'created_at' | 'updated_at'>,
): Promise<KnowledgeFAQ> {
  const res = await fetch(`${BK_BASE}/faqs`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(faq),
  })
  return handleResponse<KnowledgeFAQ>(res, 'Impossible d’ajouter la FAQ.')
}

export async function updateKnowledgeFAQ(
  token: string,
  faqId: number,
  faq: Partial<KnowledgeFAQ>,
): Promise<KnowledgeFAQ> {
  const res = await fetch(`${BK_BASE}/faqs/${faqId}`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(faq),
  })
  return handleResponse<KnowledgeFAQ>(res, 'Impossible de modifier la FAQ.')
}

export async function deleteKnowledgeFAQ(token: string, faqId: number): Promise<void> {
  const res = await fetch(`${BK_BASE}/faqs/${faqId}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
  return handleResponse<void>(res, 'Impossible de supprimer la FAQ.')
}

// ==========================================
// AI Community Manager Settings & Dashboard
// ==========================================

export async function getAICMSettings(token: string): Promise<AICMSettings> {
  const res = await fetch(`${AICM_BASE}/settings`, { headers: authHeaders(token) })
  return handleResponse<AICMSettings>(res, 'Impossible de charger les paramètres IA.')
}

export async function updateAICMSettings(
  token: string,
  settings: Partial<AICMSettings>,
): Promise<AICMSettings> {
  const res = await fetch(`${AICM_BASE}/settings`, {
    method: 'PATCH',
    headers: authHeaders(token),
    body: JSON.stringify(settings),
  })
  return handleResponse<AICMSettings>(res, 'Impossible de mettre à jour les paramètres IA.')
}

export async function getAICMDashboard(
  token: string,
  platform?: string,
  startDate?: string,
  endDate?: string,
): Promise<AICMDashboardMetrics> {
  const params = new URLSearchParams()
  if (platform && platform !== 'ALL') params.append('platform', platform)
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)

  const url = `${AICM_BASE}/dashboard?${params.toString()}`
  const res = await fetch(url, { headers: authHeaders(token) })
  return handleResponse<AICMDashboardMetrics>(res, 'Impossible de charger le tableau de bord.')
}

export async function getAICMAuditLogs(
  token: string,
  limit = 50,
  offset = 0,
  action?: string,
): Promise<AICMAuditLog[]> {
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() })
  if (action) params.append('action', action)
  const res = await fetch(`${AICM_BASE}/audit-logs?${params.toString()}`, { headers: authHeaders(token) })
  return handleResponse<AICMAuditLog[]>(res, 'Impossible de charger le journal d’audit.')
}

// ==========================================
// Drafts & Interactive Message Endpoints
// ==========================================

export async function listAICMDrafts(token: string, status?: string): Promise<AIReplyDraft[]> {
  const url = status ? `${AICM_BASE}/drafts?status=${status}` : `${AICM_BASE}/drafts`
  const res = await fetch(url, { headers: authHeaders(token) })
  return handleResponse<AIReplyDraft[]>(res, 'Impossible de charger les brouillons.')
}

export async function approveAICMDraft(
  token: string,
  draftId: number,
  approved: boolean,
  modifiedReplyText?: string,
  autoSend = true,
): Promise<AIReplyDraft> {
  const res = await fetch(`${AICM_BASE}/drafts/${draftId}/approve`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      approved,
      modified_reply_text: modifiedReplyText,
      auto_send: autoSend,
    }),
  })
  return handleResponse<AIReplyDraft>(res, 'Erreur lors de la validation du brouillon.')
}

export async function analyzeInboxMessage(
  token: string,
  messageId: number,
): Promise<AIAnalysisResult> {
  const res = await fetch(`${AICM_BASE}/messages/${messageId}/analyze`, {
    method: 'POST',
    headers: authHeaders(token),
  })
  return handleResponse<AIAnalysisResult>(res, 'Échec de l’analyse sémantique du message.')
}

export async function generateAICMReply(
  token: string,
  messageId: number,
  customInstructions?: string,
): Promise<AIReplyDraft> {
  const params = new URLSearchParams()
  if (customInstructions) params.append('custom_instructions', customInstructions)

  const res = await fetch(`${AICM_BASE}/messages/${messageId}/generate-reply?${params.toString()}`, {
    method: 'POST',
    headers: authHeaders(token),
  })
  return handleResponse<AIReplyDraft>(res, 'Échec de la génération de réponse par l’IA.')
}

export async function getAICMMessageContext(token: string, messageId: number): Promise<any> {
  const res = await fetch(`${AICM_BASE}/messages/${messageId}/context`, {
    headers: authHeaders(token),
  })
  return handleResponse<any>(res, 'Impossible de charger le contexte métier de l’interaction.')
}

export async function getAICMMessageHistory(token: string, messageId: number): Promise<any[]> {
  const res = await fetch(`${AICM_BASE}/messages/${messageId}/history`, {
    headers: authHeaders(token),
  })
  return handleResponse<any[]>(res, 'Impossible de charger l’historique des échanges.')
}

export async function escalateAICMMessage(
  token: string,
  messageId: number,
  note: string,
  escalatedToUserId?: number,
): Promise<any> {
  const res = await fetch(`${AICM_BASE}/messages/${messageId}/escalate`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      escalation_note: note,
      escalated_to_user_id: escalatedToUserId,
    }),
  })
  return handleResponse<any>(res, 'Échec de l’escalade du message.')
}

export async function assignAICMMessage(
  token: string,
  messageId: number,
  assignedToUserId?: number | null,
): Promise<any> {
  const res = await fetch(`${AICM_BASE}/messages/${messageId}/assign`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({
      assigned_to_user_id: assignedToUserId,
    }),
  })
  return handleResponse<any>(res, 'Échec de l’assignation du message.')
}
