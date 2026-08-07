import { createContext } from 'react'
import type { UserRole } from '../api/types'

export interface AuthUser {
  name: string
  role: UserRole
}

export interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
