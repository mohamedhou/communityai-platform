export type AICMMode = 'MANUAL' | 'APPROVAL_REQUIRED' | 'AUTOMATIC'

export type AIReplyDraftStatus = 'SUGGESTED' | 'APPROVED' | 'REJECTED' | 'SENT' | 'FAILED'

export type UrgencyLevel = 'low' | 'normal' | 'high' | 'critical'

export type IntentType =
  | 'question'
  | 'purchase'
  | 'price_inquiry'
  | 'complaint'
  | 'compliment'
  | 'delivery_inquiry'
  | 'support_request'
  | 'spam'

export interface ApprovedExample {
  scenario: string
  customer_message: string
  approved_reply: string
}

export interface BusinessKnowledge {
  id: number
  workspace_id: number
  company_name: string
  description: string
  industry: string
  website?: string | null
  address?: string | null
  contact_email?: string | null
  contact_phone?: string | null
  operating_hours?: string | null
  languages: string[]

  refund_policy?: string | null
  return_policy?: string | null
  warranty_policy?: string | null
  shipping_policy?: string | null
  complaint_procedure?: string | null
  support_contact?: string | null

  brand_tone: string
  writing_style?: string | null
  preferred_expressions: string[]
  forbidden_expressions: string[]
  allowed_emojis: string[]
  preferred_languages: string[]
  approved_examples: ApprovedExample[]

  created_at: string
  updated_at: string
}

export interface KnowledgeProduct {
  id: number
  workspace_id: number
  name: string
  description: string
  price: string
  availability: string
  features: string[]
  promotions?: string | null
  delivery_terms?: string | null
  created_at: string
  updated_at: string
}

export interface KnowledgeFAQ {
  id: number
  workspace_id: number
  category: string
  question: string
  answer: string
  keywords: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AICMSettings {
  id: number
  workspace_id: number
  mode: AICMMode
  enabled_platforms: string[]
  allowed_languages: string[]
  min_confidence_score: number
  auto_reply_intents: string[]
  blocked_intents: string[]
  working_hours_only: boolean
  working_hours_schedule?: Record<string, any> | null
  default_escalation_user_id?: number | null
  model_name?: string | null
  temperature: number
  created_at: string
  updated_at: string
}

export interface AIReplyDraft {
  id: number
  workspace_id: number
  inbox_message_id: number
  reply_text: string
  original_reply_text: string
  confidence_score: number
  sources_used: string[]
  status: AIReplyDraftStatus
  requires_human: boolean
  escalation_reason?: string | null
  created_by_ai: boolean
  reviewed_by_user_id?: number | null
  reviewed_at?: string | null
  sent_at?: string | null
  external_reply_id?: string | null
  error_message?: string | null
  idempotency_key?: string | null
  created_at: string
  updated_at: string
}

export interface AIAnalysisResult {
  sentiment: 'positive' | 'neutral' | 'negative'
  intent: IntentType
  language: string
  urgency: UrgencyLevel
  topic: string
  customer_need?: string | null
  potential_risk?: string | null
  requires_human: boolean
  reason: string
  confidence: number
}

export interface AICMAuditLog {
  id: number
  workspace_id: number
  inbox_message_id?: number | null
  user_id?: number | null
  action: string
  details: Record<string, any>
  created_at: string
}

export interface SentimentBreakdown {
  positive: number
  neutral: number
  negative: number
}

export interface IntentBreakdown {
  question: number
  purchase: number
  price_inquiry: number
  complaint: number
  compliment: number
  delivery_inquiry: number
  support_request: number
  spam: number
}

export interface AICMDashboardMetrics {
  total_comments_analyzed: number
  total_messages_analyzed: number
  replies_generated: number
  replies_sent: number
  replies_pending_approval: number
  urgent_messages_count: number
  escalated_conversations_count: number
  resolution_rate: number
  average_response_time_seconds?: number | null
  sentiment_breakdown: SentimentBreakdown
  intent_breakdown: IntentBreakdown
}
