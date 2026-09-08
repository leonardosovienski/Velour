import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Signup } from './Signup'
import { Billing } from './Billing'
import { ForgotPassword, ResetPassword } from './PasswordRecovery'
import { Login } from './Login'
import { AuthContext, type AuthContextValue } from '../context/authContextValue'
import { authApi, billingApi, tenantsApi } from '../api/client'
import type { BillingStatus } from '../api/types'

vi.mock('../api/client', () => ({
  authApi: { forgotPassword: vi.fn(), resetPassword: vi.fn() },
  tenantsApi: { signupConfig: vi.fn(), export: vi.fn() },
  billingApi: { status: vi.fn(), checkout: vi.fn(), portal: vi.fn() },
  getErrorDetail: () => undefined, getErrorStatus: () => 401,
}))

const context: AuthContextValue = { user: null, loading: false, login: vi.fn(), signup: vi.fn(), logout: vi.fn() }
const trial: BillingStatus = { tenant_id: 7, tenant_name: 'Salão Aurora', subscription_status: 'trialing', trial_ends_at: '2026-09-22T12:00:00', current_period_end: null, past_due_since: null, access_allowed: true, configured: true, can_manage_billing: true, has_billing_customer: false }
function show(element: React.ReactNode, entry = '/', value = context) {
  return render(<MemoryRouter initialEntries={[entry]}><AuthContext.Provider value={value}>{element}</AuthContext.Provider></MemoryRouter>)
}
beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(tenantsApi.signupConfig).mockResolvedValue({ signup_enabled: true, trial_days: 14, terms_url: 'https://example.com/terms', privacy_url: 'https://example.com/privacy', terms_version: 'v1' })
  vi.mocked(billingApi.status).mockResolvedValue(trial)
  vi.mocked(context.signup).mockResolvedValue(undefined)
})

describe('Cadastro SaaS', () => {
  it('exige consentimento e confirmação de senha, envia contrato e abre onboarding', async () => {
    const user = userEvent.setup()
    show(<Routes><Route path="/" element={<Signup />} /><Route path="/billing" element={<p>Onboarding</p>} /></Routes>)
    await screen.findByLabelText('Nome do salão')
    await user.type(screen.getByLabelText('Nome do salão'), 'Salão Aurora')
    await user.type(screen.getByLabelText('Seu nome'), 'Ana Silva')
    await user.type(screen.getByLabelText('Email de acesso'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha', { exact: true }), 'password12345')
    await user.type(screen.getByLabelText('Confirmar senha'), 'different1234')
    expect(screen.getByRole('button', { name: 'Começar período de teste' })).toBeDisabled()
    expect(screen.getByRole('link', { name: 'Termos de Uso' })).toHaveAttribute('href', 'https://example.com/terms')
    await user.click(screen.getByRole('checkbox'))
    await user.click(screen.getByRole('button', { name: 'Começar período de teste' }))
    expect(screen.getByRole('alert')).toHaveTextContent('As senhas precisam ser iguais')
    expect(context.signup).not.toHaveBeenCalled()
    await user.clear(screen.getByLabelText('Confirmar senha'))
    await user.type(screen.getByLabelText('Confirmar senha'), 'password12345')
    await user.click(screen.getByRole('button', { name: 'Começar período de teste' }))
    await screen.findByText('Onboarding')
    expect(context.signup).toHaveBeenCalledWith({ tenant_name: 'Salão Aurora', admin_name: 'Ana Silva', admin_email: 'ana@example.com', admin_password: 'password12345', accepted_terms: true })
  })
  it('fecha cadastro se os termos publicados não estão disponíveis', async () => {
    vi.mocked(tenantsApi.signupConfig).mockResolvedValue({ signup_enabled: true, trial_days: 14, terms_url: '', privacy_url: '', terms_version: '' })
    show(<Signup />)
    await screen.findByText(/Novos cadastros estão temporariamente indisponíveis/)
    expect(screen.queryByRole('button', { name: 'Começar período de teste' })).not.toBeInTheDocument()
  })
})

describe('Assinatura', () => {
  it('mantém exportação e regularização para administrador com acesso suspenso', async () => {
    vi.mocked(billingApi.status).mockResolvedValue({ ...trial, access_allowed: false })
    show(<Billing />, '/', { ...context, user: { name: 'Ana', role: 'admin' } })
    await screen.findByText('Salão Aurora')
    expect(screen.getByRole('button', { name: 'Assinar Velour' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Exportar dados do salão' })).toBeEnabled()
    expect(screen.getByRole('alert')).toHaveTextContent('Regularize a assinatura')
  })
  it('não oferece pagamento nem dados administrativos ao profissional', async () => {
    vi.mocked(billingApi.status).mockResolvedValue({ ...trial, access_allowed: false, can_manage_billing: false })
    show(<Billing />, '/', { ...context, user: { name: 'Ana', role: 'professional' } })
    await screen.findByText('Salão Aurora')
    expect(screen.queryByRole('button', { name: 'Assinar Velour' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Exportar dados do salão' })).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Peça ao administrador')
  })
  it('retorno do checkout consulta API e não considera o parâmetro de URL como pagamento', async () => {
    vi.mocked(billingApi.status).mockResolvedValue({ ...trial, access_allowed: false })
    show(<Billing />, '/billing?checkout=success', { ...context, user: { name: 'Ana', role: 'admin' } })
    await screen.findByText('Salão Aurora')
    expect(screen.getByText('Aguardando regularização')).toBeInTheDocument()
    expect(billingApi.status).toHaveBeenCalledOnce()
    expect(screen.getByRole('status')).toHaveTextContent('A confirmação pode levar alguns instantes')
  })
})

describe('Recuperação e login', () => {
  it('não revela se um email está cadastrado', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValue({ message: 'ok' })
    const user = userEvent.setup(); show(<ForgotPassword />)
    await user.type(screen.getByLabelText('Email de acesso'), 'unknown@example.com')
    await user.click(screen.getByRole('button', { name: 'Enviar link de recuperação' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Se este email estiver cadastrado')
    expect(authApi.forgotPassword).toHaveBeenCalledWith('unknown@example.com')
  })
  it('envia token e nova senha, encerrando a sessão anterior', async () => {
    vi.mocked(authApi.resetPassword).mockResolvedValue({ message: 'ok' })
    sessionStorage.setItem('access_token', 'old-token')
    const user = userEvent.setup(); show(<ResetPassword />, '/reset-password?token=one-use-token')
    await user.type(screen.getByLabelText('Nova senha'), 'password12345')
    await user.type(screen.getByLabelText('Confirmar nova senha'), 'password12345')
    await user.click(screen.getByRole('button', { name: 'Salvar nova senha' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Senha alterada')
    expect(authApi.resetPassword).toHaveBeenCalledWith('one-use-token', 'password12345')
    expect(sessionStorage.getItem('access_token')).toBeNull()
  })
  it('preserva a mensagem de credenciais inválidas na tela', async () => {
    vi.mocked(context.login).mockRejectedValue(new Error('invalid'))
    const user = userEvent.setup(); show(<Login />)
    await user.type(screen.getByLabelText('Email'), 'ana@example.com')
    await user.type(screen.getByLabelText('Senha'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Email ou senha incorretos'))
  })
})
