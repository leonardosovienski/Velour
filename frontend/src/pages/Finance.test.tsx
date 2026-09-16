import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { beforeEach, expect, it, vi } from 'vitest'
import { Finance } from './Finance'
import { financeApi } from '../api/client'
import type { FinanceOverview } from '../api/financeTypes'

vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { name: 'Admin', role: 'admin' }, logout: vi.fn() }) }))
vi.mock('./Fiscal', () => ({ Fiscal: ({ fixedScope }: { fixedScope: string }) => <p>Fiscal: {fixedScope}</p> }))
vi.mock('./Billing', () => ({ Billing: () => <p>Plano do salão</p> }))
vi.mock('../api/client', () => ({ financeApi: { overview: vi.fn(), settle: vi.fn(), addExpense: vi.fn(), payExpense: vi.fn() }, fiscalApi: { config: vi.fn().mockResolvedValue({ can_manage_platform: false }) }, getErrorDetail: () => undefined }))
const overview: FinanceOverview = { month: '2026-09', received: 50, receivable: 70, expenses_paid: 20, expenses_pending: 80, balance: 30, expenses: [], receipts: [{ id: 7, client: 'Ana', service: 'Corte', date: '2026-09-15', amount: 120, received: 50, remaining: 70, payment_method: 'pix', document_id: null, document_status: null }] }
beforeEach(() => { vi.clearAllMocks(); vi.mocked(financeApi.overview).mockResolvedValue(overview); vi.mocked(financeApi.settle).mockResolvedValue({}) })
function show(section: string) { render(<MemoryRouter><Finance section={section} /></MemoryRouter>) }

it('reúne as cinco áreas sem confundir saldo dos registros com saldo bancário', async () => {
  show('overview')
  expect(await screen.findByText('Saldo dos registros')).toBeInTheDocument()
  expect(screen.getByText(/não é saldo bancário/)).toBeInTheDocument()
  expect(screen.getByRole('navigation', { name: 'Áreas do financeiro' }).querySelectorAll('a')).toHaveLength(5)
  expect(screen.queryByText(/Administração Velour/)).not.toBeInTheDocument()
})

it('conecta o atendimento ao documento e confirma somente o recebimento', async () => {
  show('receipts')
  expect(await screen.findByRole('link', { name: 'Preparar documento' })).toHaveAttribute('href', '/finance/documents?appointment=7')
  await userEvent.click(screen.getByRole('button', { name: 'Registrar recebimento' }))
  expect(screen.getByText(/saldo de R\$\s*70,00/)).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar recebimento' }))
  await waitFor(() => expect(financeApi.settle).toHaveBeenCalledWith(7, 'pix'))
  expect(await screen.findByText('Recebimento registrado. O documento fiscal não foi alterado.')).toBeInTheDocument()
})

it('assinatura mostra os documentos recebidos, sem controles do emissor', () => {
  show('subscription')
  expect(screen.getByText('Plano do salão')).toBeInTheDocument()
  expect(screen.getByText('Fiscal: received')).toBeInTheDocument()
})

it('falha no carregamento não inventa valores zerados', async () => {
  vi.mocked(financeApi.overview).mockRejectedValue(new Error('offline'))
  show('overview')
  expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível carregar as finanças.')
  expect(screen.queryByText('Saldo dos registros')).not.toBeInTheDocument()
})
