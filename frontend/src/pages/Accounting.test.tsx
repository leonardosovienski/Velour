import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { Accounting } from './Accounting'
import { accountingApi } from '../api/client'
import type { AccountingReport } from '../api/financeTypes'

vi.mock('../api/client', () => ({ accountingApi: { report: vi.fn(), download: vi.fn() }, getErrorDetail: () => undefined }))
const report: AccountingReport = {
  month: '2026-09', notice: 'DEMONSTRAÇÃO ACADÊMICA — SEM VALIDADE CONTÁBIL OU FISCAL.', iss_rate: 2, result: 46, total_debit: 200, total_credit: 200, chart_of_accounts: [],
  dre: [{ label: 'Receita bruta de serviços', value: 200, level: 0 }, { label: 'Resultado do período', value: 46, level: 0 }],
  entries: [{ date: '2026-09-15', history: 'Atendimento #1 — Corte (Ana)', debit: '1.1.2', credit: '3.1.1', amount: 200 }],
  trial_balance: [{ code: '1.1.2', name: 'Clientes a receber', debit: 200, credit: 0, balance: 200, nature: 'D' }, { code: '3.1.1', name: 'Receita de serviços', debit: 0, credit: 200, balance: 200, nature: 'C' }],
}
beforeEach(() => { vi.clearAllMocks(); vi.mocked(accountingApi.report).mockResolvedValue(report); vi.mocked(accountingApi.download).mockResolvedValue(new Blob(['x'])) })

it('mostra DRE, balancete e diário com aviso de demonstração', async () => {
  render(<Accounting month="2026-09" />)
  expect(await screen.findByText('Resultado do período')).toBeInTheDocument()
  expect(screen.getByText(/SEM VALIDADE/)).toBeInTheDocument()
  expect(screen.getByText('Débitos = créditos')).toBeInTheDocument()
  expect(screen.getByText('Atendimento #1 — Corte (Ana)')).toBeInTheDocument()
  expect(accountingApi.report).toHaveBeenCalledWith('2026-09')
})

it('baixa o relatório em PDF e TXT', async () => {
  URL.createObjectURL = vi.fn(() => 'blob:x'); URL.revokeObjectURL = vi.fn()
  render(<Accounting month="2026-09" />)
  await userEvent.click(await screen.findByRole('button', { name: 'Baixar PDF' }))
  await userEvent.click(screen.getByRole('button', { name: 'Baixar TXT' }))
  await waitFor(() => expect(accountingApi.download).toHaveBeenCalledTimes(2))
  expect(accountingApi.download).toHaveBeenNthCalledWith(1, '2026-09', 'pdf')
  expect(accountingApi.download).toHaveBeenNthCalledWith(2, '2026-09', 'txt')
})

it('erro de carregamento não mostra valores inventados', async () => {
  vi.mocked(accountingApi.report).mockRejectedValue(new Error('offline'))
  render(<Accounting month="2026-09" />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível carregar a contabilidade.')
  expect(screen.queryByText('Resultado do período')).not.toBeInTheDocument()
})
