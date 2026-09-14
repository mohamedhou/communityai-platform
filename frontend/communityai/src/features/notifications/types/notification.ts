export type NotificationType =
  | 'POST_PUBLISHED'
  | 'POST_FAILED'
  | 'POST_SCHEDULED'
  | 'INBOX_MESSAGE'
  | 'AI_SUGGESTION'
  | 'SOCIAL_ACCOUNT'
  | 'ANALYTICS'
  | 'SYSTEM'

export type NotificationSeverity = 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR'

export interface Notification {
  id: number
  type: NotificationType
  title: string
  message: string
  severity: NotificationSeverity
  is_read: boolean
  action_url?: string | null
  entity_type?: string | null
  entity_id?: string | null
  created_at: string
  read_at?: string | null
}

export interface NotificationListResponse {
  items: Notification[]
  total: number
  unread_count: number
  page: number
  limit: number
}

export interface NotificationUnreadCountResponse {
  unread_count: number
}

export interface NotificationFilters {
  type?: NotificationType
  severity?: NotificationSeverity
  is_read?: boolean
  page?: number
  limit?: number
}