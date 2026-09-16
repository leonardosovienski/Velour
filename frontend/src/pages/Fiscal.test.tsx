import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { beforeEach, expect, it, vi } from 'vitest'
import { Fiscal } from './Fiscal'
import { fiscalApi } from '../api/client'
import type { FiscalDocument, FiscalProfile } from '../api/fiscalTypes'

vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { name: 'Admin', role: 'admin' }, logout: vi.fn() }) }))
vi.mock('../api/client', () => ({ fiscalApi: { config: vi.fn(), profile: vi.fn(), list: vi.fn(), appointments: vi.fn(), tenants: vi.fn(), create: vi.fn(), events: vi.fn(), simulate: vi.fn(), cancel: vi.fn(), saveProfile: vi.fn(), print: vi.fn() }, getErrorDetail: () => undefined }))

const profile: FiscalProfile = { legal_name: 'Salão fictício', tax_id: '11222333000181', email: null, street: 'Rua teste', number: '10', district: 'Centro', postal_code: '83702000', city: 'Araucária', municipality_code: '4101804', state: 'PR', municipal_registration: '', tax_regime: 'simples', service_code: '060101', iss_rate: 2 }
const doc: FiscalDocument = { id: 1, tenant_id: 1, issuer_kind: 'salon', source_key: 'appointment:1', appointment_id: 1, status: 'draft', environment: 'demo', number: null, competence: '2026-09-15', description: 'Corte de cabelo', service_code: '060101', amount: 120, iss_rate: 2, iss_amount: 2.4, issuer: profile, recipient: { ...profile, legal_name: 'Cliente teste' }, created_at: '2026-09-15T12:00:00', issued_at: null, cancelled_at: null, cancellation_reason: null }

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(fiscalApi.config).mockResolvedValue({ mode: 'demo', notice: 'Demonstração', real_issuance_available: false, can_manage_platform: false })
  vi.mocked(fiscalApi.profile).mockResolvedValue(profile)
  vi.mocked(fiscalApi.list).mockResolvedValue([doc])
  vi.mocked(fiscalApi.appointments).mockResolvedValue([])
  vi.mocked(fiscalApi.events).mockResolvedValue([{ id: 1, action: 'created', created_at: '2026-09-15T12:00:00' }])
})

function open() { render(<MemoryRouter><Fiscal /></MemoryRouter>) }

it('identifica a demonstração, consulta o rascunho e emite sem sugerir autorização fiscal', async () => {
  vi.mocked(fiscalApi.simulate).mockResolvedValue({ ...doc, status: 'simulated', number: 'DEMO-00000001' })
  open()
  expect(screen.getByText('Demonstração — sem validade fiscal')).toBeInTheDocument()
  await userEvent.click(await screen.findByRole('button', { name: 'Rascunho #1' }))
  await userEvent.click(await screen.findByRole('button', { name: 'Emitir demonstração' }))
  await waitFor(() => expect(fiscalApi.simulate).toHaveBeenCalledWith(1, false))
  expect(await screen.findByText('Emissão simulada concluída. Documento sem validade fiscal.')).toBeInTheDocument()
})

it('notas recebidas não oferecem emissão ou cancelamento ao tomador', async () => {
  vi.mocked(fiscalApi.list).mockResolvedValue([{ ...doc, issuer_kind: 'platform', status: 'simulated', number: 'DEMO-00000001' }])
  open()
  await screen.findByRole('button', { name: 'DEMO-00000001' })
  await userEvent.click(screen.getByRole('tab', { name: 'Notas recebidas do Velour' }))
  await userEvent.click(await screen.findByRole('button', { name: 'DEMO-00000001' }))
  expect(await screen.findByRole('button', { name: 'Baixar demonstrativo' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Emitir demonstração' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Cancelar documento' })).not.toBeInTheDocument()
  expect(screen.queryByRole('tab', { name: 'Velour → assinantes' })).not.toBeInTheDocument()
})

it('módulo desativado mantém histórico e bloqueia novos documentos', async () => {
  vi.mocked(fiscalApi.config).mockResolvedValue({ mode: 'disabled', notice: 'Demonstração', real_issuance_available: false, can_manage_platform: false })
  open()
  expect(await screen.findByRole('button', { name: 'Novo documento' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Editar cadastro fiscal' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Rascunho #1' })).toBeInTheDocument()
})
