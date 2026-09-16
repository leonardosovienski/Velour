import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { beforeEach, expect, it, vi } from 'vitest'
import { Dashboard } from './Dashboard'
import { Clients } from './Clients'
import { clientsApi, dashboardApi } from '../api/client'

vi.mock('../context/useAuth', () => ({ useAuth: () => ({ user: { name: 'Admin', role: 'admin' }, logout: vi.fn() }) }))
vi.mock('../api/client', () => ({ clientsApi: { list: vi.fn() }, dashboardApi: { today: vi.fn(), kpis: vi.fn(), weeklyRevenue: vi.fn(), alerts: vi.fn() }, getErrorDetail: () => undefined }))
beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(dashboardApi.kpis).mockResolvedValue({} as never)
  vi.mocked(dashboardApi.weeklyRevenue).mockResolvedValue([])
  vi.mocked(dashboardApi.alerts).mockResolvedValue({} as never)
})

it('falha no painel mostra recuperação e não métricas falsas de valor zero', async () => {
  vi.mocked(dashboardApi.today).mockRejectedValue(new Error('offline'))
  render(<MemoryRouter><Dashboard /></MemoryRouter>)
  expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível carregar os dados')
  expect(screen.queryByText('Receita hoje')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Tentar novamente' })).toBeEnabled()
})

it('lista de clientes encerra carregamento após falha e permite repetir a consulta', async () => {
  vi.mocked(clientsApi.list).mockRejectedValueOnce(new Error('offline')).mockResolvedValue([])
  render(<MemoryRouter><Clients /></MemoryRouter>)
  await userEvent.click(await screen.findByRole('button', { name: 'Tentar novamente' }))
  await waitFor(() => expect(clientsApi.list).toHaveBeenCalledTimes(2))
  await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
})
