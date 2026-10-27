export type AIAction =
  | 'GENERATE'
  | 'REWRITE'
  | 'IMPROVE'
  | 'SHORTEN'
  | 'EXPAND'
  | 'CHANGE_TONE'
  | 'ADAPT_PLATFORM'
  | 'IDEATE'

export type AITone =
  | 'FORMAL'
  | 'PROFESSIONAL'
  | 'CASUAL'
  | 'FRIENDLY'
  | 'TECHNICAL'
  | 'PROMOTIONAL'
  | 'HUMOROUS'

export type AIPlatform = 'FACEBOOK' | 'INSTAGRAM' | 'LINKEDIN'

export interface AIUsage {
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
}

export interface AIResponse {
  content: string
  action: AIAction
  usage?: AIUsage | null
  ideas?: string[] | null
}

export interface AIProviderStatus {
  provider: string
  model: string
  available: boolean
  base_url?: string | null
  error?: string | null
  installed_models?: string[]
}

export interface AIGeneratePayload {
  prompt: string
  platform?: AIPlatform
  tone?: AITone
  audience?: string
  objective?: string
  editorial_context?: string
  language?: string
  length?: string
  include_hashtags?: boolean
  include_cta?: boolean
}

export interface AIRewritePayload {
  content: string
  tone?: AITone
  platform?: AIPlatform
  editorial_context?: string
  language?: string
  include_hashtags?: boolean
  include_cta?: boolean
}

export interface AIImprovePayload {
  content: string
  platform?: AIPlatform
  editorial_context?: string
  language?: string
  include_hashtags?: boolean
  include_cta?: boolean
}

export interface AIShortenPayload {
  content: string
  platform?: AIPlatform
  editorial_context?: string
  language?: string
}

export interface AIExpandPayload {
  content: string
  platform?: AIPlatform
  editorial_context?: string
  language?: string
  include_hashtags?: boolean
  include_cta?: boolean
}

export interface AIChangeTonePayload {
  content: string
  tone: AITone
  platform?: AIPlatform
  editorial_context?: string
  language?: string
}

export interface AIAdaptPlatformPayload {
  content: string
  platform: AIPlatform
  tone?: AITone
  editorial_context?: string
  language?: string
  include_hashtags?: boolean
  include_cta?: boolean
}

export interface AIIdeasPayload {
  topic: string
  platform?: AIPlatform
  tone?: AITone
  target_audience?: string
  editorial_context?: string
  language?: string
}

export interface AIHistoryItem {
  id: string
  action: AIAction
  platform?: AIPlatform
  tone?: AITone
  inputSnippet: string
  result: AIResponse
  timestamp: string
}
