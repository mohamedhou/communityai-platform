export type UserRole = 'ADMIN' | 'COMMUNITY_MANAGER' | 'CLIENT'

export type AuthUser = {
  id: number
  email: string
  first_name: string
  last_name: string
  role: UserRole
  is_active: boolean
}

export type LoginRequest = {
  email: string
  password: string
}

export type RegisterRequest = {
  email: string
  password: string
  first_name: string
  last_name: string
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}
