import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { Costs } from './Costs'
import { costsApi } from '../api/client'
import type { CostLine, CostReport } from '../api/financeTypes'

vi.mock('../api/client', () => ({ costsApi: { report: vi.fn(), saveBudget: vi.fn(), download: vi.fn() }, getErrorDetail: () => undefined }))
const line = (category: CostLine['category'], label: string, kind: CostLine['kind'], actual: number, budget: number | null = null): CostLine => ({
  category, label, kind, actual, budget, variance: budget === null ? null : actual - budget, consumed_ratio: budget ? actual / budget : null,
  status: budget === null ? 'no_budget' : actual > budget ? 'over' : 'within',
})
const report: CostReport = {
  month: '2026-09', notice: 'Visão gerencial calculada a partir dos registros do Velour.', iss_rate: 2, budget_total: 60,
  summary: { appointments: 1, revenue: 200, variable_costs: 104, contribution_margin: 96, contribution_margin_ratio: 0.48, fixed_costs: 50, result: 46, average_ticket: 200, cost_per_appointment: 154, break_even_revenue: 104.17, break_even_appointments: 1, safety_margin: 0.4792 },
  lines: [line('inputs', 'Insumos consumidos', 'variable', 20), line('commissions', 'Comissões de profissionais', 'variable', 80, 60), line('taxes', 'ISS estimado', 'variable', 4), line('rent', 'Aluguel', 'fixed', 50)],
  services: [{ id: 1, name: 'Coloração', category: 'Cabelo', appointments: 1, revenue: 200, inputs: 20, commissions: 80, taxes: 4, contribution_margin: 96, margin_ratio: 0.48 }],
  professionals: [{ id: 3, name: 'Bianca', commission_rate: 0.4, appointments: 1, revenue: 200, inputs: 20, commissions: 80, taxes: 4, contribution_margin: 96, margin_ratio: 0.48 }],
  standard_costs: [{ id: 1, name: 'Coloração', price: 100, recipe_items: 1, standard_input_cost: 20, input_ratio: 0.2, taxes: 2, margin_before_commission: 78 }],
  history: [{ month: '2026-08', appointments: 0, revenue: 0, variable_costs: 0, fixed_costs: 0, result: 0 }, { month: '2026-09', appointments: 1, revenue: 200, variable_costs: 104, fixed_costs: 50, result: 46 }],
  alerts: [{ level: 'warning', message: 'Comissões de profissionais acima do orçamento em R$ 20,00.' }],
}
beforeEach(() => { vi.clearAllMocks(); vi.mocked(costsApi.report).mockResolvedValue(report); vi.mocked(costsApi.saveBudget).mockResolvedValue({ month: '2026-09', items: [] }); vi.mocked(costsApi.download).mockResolvedValue(new Blob(['x'])) })

it('mostra indicadores, alertas e orçado × realizado com texto, sem depender só de cor', async () => {
  render(<Costs month="2026-09" />)
  expect(await screen.findByText('Margem de contribuição')).toBeInTheDocument()
  expect(costsApi.report).toHaveBeenCalledWith('2026-09')
  expect(screen.getByText(/48% da receita/)).toBeInTheDocument()
  expect(screen.getByText('Cerca de 1 atendimento')).toBeInTheDocument()
  expect(screen.getByText('Comissões de profissionais acima do orçamento em R$ 20,00.')).toBeInTheDocument()
  const budget = screen.getByRole('table', { name: 'Custos realizados comparados ao orçamento do mês' })
  expect(within(budget).getByText('Acima do orçamento')).toBeInTheDocument()
  expect(within(budget).getAllByText('Sem orçamento')).toHaveLength(3)
  expect(screen.getByRole('table', { name: /margem antes da comissão/ })).toHaveTextContent('1 insumo · 20% do preço')
  expect(screen.getByRole('table', { name: 'Receita, custos e resultado por mês' })).toHaveTextContent('09/2026')
})

it('salva o orçamento do mês só com as linhas preenchidas', async () => {
  render(<Costs month="2026-09" />)
  await userEvent.click(await screen.findByRole('button', { name: 'Definir orçamento do mês' }))
  expect(screen.getByLabelText('Comissões de profissionais (R$)')).toHaveValue(60)
  await userEvent.type(screen.getByLabelText('Aluguel (R$)'), '800')
  await userEvent.click(screen.getByRole('button', { name: 'Salvar orçamento' }))
  await waitFor(() => expect(costsApi.saveBudget).toHaveBeenCalledWith('2026-09', [{ category: 'commissions', amount: 60 }, { category: 'rent', amount: 800 }]))
  expect(await screen.findByText('Orçamento do mês salvo.')).toBeInTheDocument()
  expect(costsApi.report).toHaveBeenCalledTimes(2)
})

it('baixa a planilha do mês', async () => {
  URL.createObjectURL = vi.fn(() => 'blob:x'); URL.revokeObjectURL = vi.fn()
  render(<Costs month="2026-09" />)
  await userEvent.click(await screen.findByRole('button', { name: 'Baixar planilha (CSV)' }))
  await waitFor(() => expect(costsApi.download).toHaveBeenCalledWith('2026-09'))
})

it('falha no carregamento não mostra indicadores zerados', async () => {
  vi.mocked(costsApi.report).mockRejectedValue(new Error('offline'))
  render(<Costs month="2026-09" />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível carregar a gestão de custos.')
  expect(screen.queryByText('Margem de contribuição')).not.toBeInTheDocument()
})
