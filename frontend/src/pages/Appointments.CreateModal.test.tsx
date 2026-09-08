import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { CreateModal } from './Appointments'

const createMock = vi.fn().mockResolvedValue({})

vi.mock('../api/client', () => ({
  appointmentsApi: { create: (...args: unknown[]) => createMock(...args) },
  clientsApi: { list: vi.fn().mockResolvedValue([{ id: 1, name: 'Cliente Teste', code: 'VLR-00001' }]) },
  professionalsApi: { list: vi.fn().mockResolvedValue([{ id: 2, name: 'Profissional Teste', specialty: 'Corte' }]) },
  servicesApi: { list: vi.fn().mockResolvedValue([{ id: 3, name: 'Corte', duration_minutes: 60, price: 100.1, points_reward: 0 }]) },
  recipesApi: {},
  getErrorDetail: () => undefined,
}))

it('envia a data e hora digitadas no salão sem converter para UTC', async () => {
  const user = userEvent.setup()
  const success = vi.fn()
  render(<CreateModal open onClose={() => {}} onSuccess={success} />)
  await screen.findByRole('option', { name: 'Cliente Teste (VLR-00001)' })
  await user.selectOptions(screen.getByLabelText('Cliente *'), '1')
  await user.selectOptions(screen.getByLabelText('Profissional *'), '2')
  await user.selectOptions(screen.getByLabelText('Serviço *'), '3')
  fireEvent.change(screen.getByLabelText('Data e horário do salão *'), { target: { value: '2030-02-05T23:30' } })
  await user.click(screen.getByRole('button', { name: 'Agendar' }))
  await waitFor(() => expect(createMock).toHaveBeenCalledOnce())
  expect(createMock).toHaveBeenCalledWith(expect.objectContaining({
    client_id: 1, professional_id: 2, service_id: 3, scheduled_at: '2030-02-05T23:30',
  }))
  expect(success).toHaveBeenCalledOnce()
})
