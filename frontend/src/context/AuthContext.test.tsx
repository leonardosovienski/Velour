import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useContext } from 'react'
import { AuthProvider } from './AuthContext'
import { AuthContext } from './authContextValue'
import { authApi, tenantsApi } from '../api/client'

vi.mock('../api/client', () => ({
  authApi: { login: vi.fn(), me: vi.fn() },
  tenantsApi: { signup: vi.fn() },
}))

const session = { access_token: 'fake-token', token_type: 'bearer', role: 'admin' as const, name: 'Admin Teste' }
function Probe() {
  const ctx = useContext(AuthContext)!
  return <div>
    <span data-testid="user">{ctx.user ? `${ctx.user.name}:${ctx.user.role}` : 'sem-usuario'}</span>
    <span data-testid="loading">{String(ctx.loading)}</span>
    <button onClick={() => ctx.login('admin@velour.com', 'password12345')}>entrar</button>
    <button onClick={() => ctx.signup({ tenant_name: 'Salão', admin_name: 'Admin Teste', admin_email: 'admin@velour.com', admin_password: 'password12345', accepted_terms: true })}>cadastrar</button>
    <button onClick={() => ctx.logout()}>sair</button>
  </div>
}

describe('AuthProvider', () => {
  beforeEach(() => { localStorage.clear(); sessionStorage.clear(); vi.clearAllMocks(); vi.mocked(authApi.login).mockResolvedValue(session); vi.mocked(tenantsApi.signup).mockResolvedValue(session) })
  it('remove credenciais persistentes legadas sem confiar no perfil salvo', async () => {
    localStorage.setItem('access_token', 'old-token'); localStorage.setItem('user_role', 'admin')
    render(<AuthProvider><Probe /></AuthProvider>)
    expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(authApi.me).not.toHaveBeenCalled()
  })
  it('login mantém apenas o token na sessão e logout o remove', async () => {
    const user = userEvent.setup(); render(<AuthProvider><Probe /></AuthProvider>)
    await user.click(screen.getByText('entrar'))
    expect(screen.getByTestId('user')).toHaveTextContent('Admin Teste:admin')
    expect(sessionStorage.getItem('access_token')).toBe('fake-token')
    expect(localStorage.getItem('access_token')).toBeNull()
    await user.click(screen.getByText('sair'))
    expect(sessionStorage.getItem('access_token')).toBeNull()
    expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario')
  })
  it('valida o usuário no servidor ao restaurar uma sessão', async () => {
    sessionStorage.setItem('access_token', 'valid-token')
    vi.mocked(authApi.me).mockResolvedValue({ ...session, role: 'professional', id: 1, email: 'ana@example.com', is_active: true, created_at: '' })
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Admin Teste:professional'))
    expect(authApi.me).toHaveBeenCalledOnce()
  })
  it('o cadastro estabelece a sessão e um evento 401 limpa o contexto', async () => {
    render(<AuthProvider><Probe /></AuthProvider>)
    await userEvent.setup().click(screen.getByText('cadastrar'))
    expect(sessionStorage.getItem('access_token')).toBe('fake-token')
    act(() => { window.dispatchEvent(new Event('velour:session-expired')) })
    expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario')
  })
})
