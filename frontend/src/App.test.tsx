import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./api/client', async importOriginal => {
  const original = await importOriginal<typeof import('./api/client')>()
  return {
    ...original,
    authApi: { ...original.authApi, me: vi.fn().mockResolvedValue({ name: 'Ana', role: 'admin' }) },
    billingApi: { ...original.billingApi, status: vi.fn().mockResolvedValue({ tenant_id: 1, tenant_name: 'Salão teste', subscription_status: 'trialing', trial_ends_at: null, current_period_end: null, access_allowed: false, configured: false, can_manage_billing: true, has_billing_customer: false }) },
  }
})
vi.mock('./pages/Dashboard', () => ({ Dashboard: () => <button onClick={() => window.dispatchEvent(new Event('velour:subscription-required'))}>Simular período encerrado</button> }))

beforeEach(() => { sessionStorage.clear(); localStorage.clear(); window.history.replaceState({}, '', '/') })

it('encaminha HTTP 402 para cobrança mantendo sessão e acesso à exportação', async () => {
  sessionStorage.setItem('access_token', 'valid-token')
  render(<App />)
  await userEvent.setup().click(await screen.findByRole('button', { name: 'Simular período encerrado' }))
  expect(await screen.findByRole('heading', { name: 'Conta e assinatura' })).toBeInTheDocument()
  expect(await screen.findByRole('button', { name: 'Exportar dados do salão' })).toBeInTheDocument()
  expect(window.location.pathname).toBe('/billing')
  expect(sessionStorage.getItem('access_token')).toBe('valid-token')
})

it('rota protegida sem sessão abre login com links de cadastro e recuperação', async () => {
  window.history.replaceState({}, '', '/billing')
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Bem-vindo de volta' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Criar conta' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Esqueci minha senha' })).toBeInTheDocument()
})

it('uma sessão estabelecida pelo cadastro abre onboarding sem redirecionar ao painel', async () => {
  window.history.replaceState({}, '', '/signup')
  sessionStorage.setItem('access_token', 'new-signup-token')
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Seu salão está pronto para começar' })).toBeInTheDocument()
  expect(window.location.pathname + window.location.search).toBe('/billing?welcome=1')
})
