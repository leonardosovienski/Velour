import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useContext } from 'react'
import { AuthProvider } from './AuthContext'
import { AuthContext } from './authContextValue'

vi.mock('../api/client', () => ({
  authApi: {
    login: vi.fn(async (email: string) => ({
      access_token: 'fake-token',
      token_type: 'bearer',
      role: 'admin',
      name: email === 'admin@velour.com' ? 'Admin Teste' : 'Outro',
      professional_id: null,
    })),
  },
}))

function Probe() {
  const ctx = useContext(AuthContext)
  if (!ctx) return null
  return (
    <div>
      <span data-testid="user">{ctx.user ? `${ctx.user.name}:${ctx.user.role}` : 'sem-usuario'}</span>
      <button onClick={() => ctx.login('admin@velour.com', 'senha123')}>entrar</button>
      <button onClick={() => ctx.logout()}>sair</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('inicia sem usuário quando não há token salvo', async () => {
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario'))
  })

  it('login persiste no localStorage e atualiza o usuário no contexto', async () => {
    const user = userEvent.setup()
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario'))

    await act(async () => {
      await user.click(screen.getByText('entrar'))
    })

    expect(screen.getByTestId('user')).toHaveTextContent('Admin Teste:admin')
    expect(localStorage.getItem('access_token')).toBe('fake-token')
    expect(localStorage.getItem('user_role')).toBe('admin')
  })

  it('logout limpa o localStorage e o usuário do contexto', async () => {
    const user = userEvent.setup()
    render(<AuthProvider><Probe /></AuthProvider>)
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario'))

    await act(async () => {
      await user.click(screen.getByText('entrar'))
    })
    expect(screen.getByTestId('user')).not.toHaveTextContent('sem-usuario')

    await act(async () => {
      await user.click(screen.getByText('sair'))
    })

    expect(screen.getByTestId('user')).toHaveTextContent('sem-usuario')
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
