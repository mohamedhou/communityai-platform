import type { UserRole } from '../../auth/types/auth'

export type ProfileUpdateRequest = {
  first_name: string
  last_name: string
}

export type ChangePasswordRequest = {
  current_password: string
  new_password: string
}

export type UserStatusUpdateRequest = {
  is_active: boolean
}

export type UserRoleUpdateRequest = {
  role: UserRole
}
