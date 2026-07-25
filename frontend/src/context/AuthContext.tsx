import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { authApi } from '../api/client'
import type { UserRole } from '../api/types'

interface AuthUser {
  name: string
  role: UserRole
}

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const name = localStorage.getItem('user_name')
    const role = localStorage.getItem('user_role') as UserRole | null
    if (token && name && role) setUser({ name, role })
    setLoading(false)
  }, [])

  async function login(email: string, password: string) {
    const data = await authApi.login(email, password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user_name', data.name)
    localStorage.setItem('user_role', data.role)
    setUser({ name: data.name, role: data.role })
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_name')
    localStorage.removeItem('user_role')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
