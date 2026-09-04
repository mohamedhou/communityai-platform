export type InboxMessageType = 'COMMENT' | 'MESSAGE' | 'MENTION'

export type InboxSentiment = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE' | 'UNKNOWN'

export interface SocialAccountSummary {
  id: number
  platform: string
  provider: string
  account_name: string
  account_username?: string | null
  profile_image_url?: string | null
}

export interface InboxMessage {
  id: number
  user_id: number
  social_account_id: number
  external_id: string
  type: InboxMessageType
  sender_name: string
  sender_external_id?: string | null
  content: string
  sentiment: InboxSentiment
  sentiment_score?: number | null
  is_read: boolean
  is_resolved: boolean
  replied_at?: string | null
  created_at: string
  updated_at: string
  social_account?: SocialAccountSummary | null
}

export interface InboxListResponse {
  items: InboxMessage[]
  total: number
  unread_count: number
}

export interface InboxUnreadCountResponse {
  unread_count: number
}

export interface InboxFiltersState {
  type?: InboxMessageType | 'ALL'
  platform?: string
  sentiment?: InboxSentiment | 'ALL'
  status?: 'ALL' | 'UNREAD' | 'READ' | 'RESOLVED'
  search?: string
}

export interface InboxReplyRequest {
  content: string
}

export interface InboxSuggestReplyRequest {
  tone?: string
  instructions?: string
}
