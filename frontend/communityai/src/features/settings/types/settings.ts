export type UserRole = 'ADMIN' | 'COMMUNITY_MANAGER' | 'CLIENT'

export interface UserSettings {
  id: number
  user_id: number
  email: string
  first_name: string
  last_name: string
  role: UserRole
  workspace_name: string
  workspace_description: string | null
  timezone: string
  language: string
  default_platform: string | null
  notifications_enabled: boolean
  post_notifications_enabled: boolean
  inbox_notifications_enabled: boolean
  social_notifications_enabled: boolean
  analytics_notifications_enabled: boolean
  connected_account_count: number
  created_at: string
  updated_at: string
}

export type UserSettingsUpdate = Partial<Pick<
  UserSettings,
  | 'first_name'
  | 'last_name'
  | 'workspace_name'
  | 'workspace_description'
  | 'timezone'
  | 'language'
  | 'default_platform'
  | 'notifications_enabled'
  | 'post_notifications_enabled'
  | 'inbox_notifications_enabled'
  | 'social_notifications_enabled'
  | 'analytics_notifications_enabled'
>>

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface ChangePasswordResponse {
  message: string
}