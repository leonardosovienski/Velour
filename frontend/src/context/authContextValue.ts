import { createContext } from 'react'
import type { UserRole, SignupRequest } from '../api/types'

export interface AuthUser {
  name: string
  role: UserRole
}

export interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (body: SignupRequest) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
