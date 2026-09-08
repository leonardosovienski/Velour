import { useState, useEffect, type ReactNode } from 'react'
import { authApi, tenantsApi } from '../api/client'
import type { LoginResponse, SignupRequest } from '../api/types'
import { AuthContext, type AuthUser } from './authContextValue'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    // Remove legacy persistent credentials; identity is always validated by the API.
    for (const key of ['access_token', 'user_name', 'user_role']) localStorage.removeItem(key)
    function expire() { setUser(null) }
    window.addEventListener('velour:session-expired', expire)
    if (sessionStorage.getItem('access_token')) {
      authApi.me().then(data => {
        if (active) setUser({ name: data.name, role: data.role })
      }).catch(() => {
        if (active) setUser(null)
      }).finally(() => { if (active) setLoading(false) })
    } else {
      setLoading(false)
    }
    return () => {
      active = false
      window.removeEventListener('velour:session-expired', expire)
    }
  }, [])

  function acceptSession(data: LoginResponse) {
    sessionStorage.setItem('access_token', data.access_token)
    setUser({ name: data.name, role: data.role })
  }

  async function login(email: string, password: string) {
    acceptSession(await authApi.login(email.trim(), password))
  }

  async function signup(body: SignupRequest) {
    acceptSession(await tenantsApi.signup(body))
  }

  function logout() {
    sessionStorage.removeItem('access_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
