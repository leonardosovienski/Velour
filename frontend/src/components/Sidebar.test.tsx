import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import { Sidebar } from './Sidebar'
import { AuthContext } from '../context/authContextValue'

vi.mock('../context/useAuth', () => ({
  useAuth: () => ({
    user: { name: 'Ana Teste', role: 'admin' },
    logout: vi.fn(),
  }),
}))

describe('Sidebar', () => {
  it('expõe um landmark de navegação com aria-label', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: { name: 'Ana Teste', role: 'admin' }, loading: false, login: vi.fn(), logout: vi.fn() }}>
          <Sidebar />
        </AuthContext.Provider>
      </MemoryRouter>
    )
    expect(screen.getByRole('navigation', { name: 'Navegação principal' })).toBeInTheDocument()
  })

  it('o botão de fechar do drawer mobile tem aria-label', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ user: { name: 'Ana Teste', role: 'admin' }, loading: false, login: vi.fn(), logout: vi.fn() }}>
          <Sidebar onClose={() => {}} />
        </AuthContext.Provider>
      </MemoryRouter>
    )
    expect(screen.getByRole('button', { name: 'Fechar menu' })).toBeInTheDocument()
  })
})
