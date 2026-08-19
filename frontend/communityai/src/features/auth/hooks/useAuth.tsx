import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import * as authApi from '../services/authApi'
import type { AuthUser, LoginRequest, RegisterRequest } from '../types/auth'

type AuthContextValue = {
  user: AuthUser | null
  accessToken: string | null
  isBootstrapping: boolean
  register: (payload: RegisterRequest) => Promise<void>
  login: (payload: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  updateCurrentUser: (updatedUser: AuthUser) => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  const clearAuth = useCallback(() => {
    setUser(null)
    setAccessToken(null)
  }, [])

  const bootstrapSession = useCallback(async () => {
    try {
      const refreshed = await authApi.refresh()
      setAccessToken(refreshed.access_token)
      const me = await authApi.getMe(refreshed.access_token)
      setUser(me)
    } catch {
      clearAuth()
    } finally {
      setIsBootstrapping(false)
    }
  }, [clearAuth])

  useEffect(() => {
    void bootstrapSession()
  }, [bootstrapSession])

  const register = useCallback(async (payload: RegisterRequest) => {
    await authApi.register(payload)
  }, [])

  const login = useCallback(async (payload: LoginRequest) => {
    const tokens = await authApi.login(payload)
    setAccessToken(tokens.access_token)
    const me = await authApi.getMe(tokens.access_token)
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      clearAuth()
    }
  }, [clearAuth])

  const updateCurrentUser = useCallback((updatedUser: AuthUser) => {
    setUser(updatedUser)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isBootstrapping,
      register,
      login,
      logout,
      updateCurrentUser,
    }),
    [accessToken, isBootstrapping, login, logout, register, user, updateCurrentUser],
  )


  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
