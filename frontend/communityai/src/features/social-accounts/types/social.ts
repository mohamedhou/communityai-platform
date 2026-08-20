export type SocialAccountStatus = 'CONNECTED' | 'EXPIRED' | 'REVOKED' | 'ERROR'

export type SocialAccount = {
  id: number
  platform: string
  provider: string
  account_name: string
  account_username: string | null
  profile_image_url: string | null
  status: SocialAccountStatus
  token_expires_at: string | null
  created_at: string
  updated_at: string
}
