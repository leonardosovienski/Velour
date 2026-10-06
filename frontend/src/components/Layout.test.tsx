import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { expect, it, vi } from 'vitest'
import { Layout } from './Layout'

vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { name: 'Ana Teste', role: 'admin' }, logout: vi.fn() }) }))

it('o primeiro Tab leva ao atalho para o conteúdo principal', async () => {
  render(<MemoryRouter><Layout><p>Conteúdo da página</p></Layout></MemoryRouter>)
  await userEvent.tab()
  const skip = screen.getByRole('link', { name: 'Pular para o conteúdo' })
  expect(skip).toHaveFocus()
  expect(skip).toHaveAttribute('href', '#conteudo')
  expect(screen.getByRole('main')).toHaveAttribute('id', 'conteudo')
  expect(screen.getByRole('main')).toHaveTextContent('Conteúdo da página')
})
