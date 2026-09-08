import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { CompleteModal } from './Appointments'
import type { AppointmentDetail } from '../api/types'

const completeMock = vi.fn().mockResolvedValue({})
const uploadPhotosMock = vi.fn().mockResolvedValue({})

vi.mock('../api/client', () => ({
  appointmentsApi: {
    complete: (...args: unknown[]) => completeMock(...args),
    uploadPhotos: (...args: unknown[]) => uploadPhotosMock(...args),
  },
  recipesApi: {
    get: vi.fn().mockResolvedValue([]),
  },
  getErrorDetail: () => undefined,
}))

const appt: AppointmentDetail = {
  id: 1,
  client_id: 1,
  professional_id: 1,
  service_id: 1,
  scheduled_at: '2027-01-01T10:00:00',
  ends_at: '2027-01-01T11:00:00',
  status: 'confirmed',
  points_awarded: 0,
  discount_points_used: 0,
  tier_discount_amount: 0,
  paid: false,
  created_at: '2027-01-01T09:00:00',
  client: {
    id: 1,
    code: 'VLR-00001',
    name: 'Cliente Teste',
    phone: '11999999999',
    gender: 'F',
    chat_preference: 'neutral',
    loyalty_points: 500,
    loyalty_tier: 'gold',
    total_spent: 2000,
    total_visits: 5,
    referral_code: 'ABC12345',
    is_active: true,
    first_visit: '2026-01-01',
  } as AppointmentDetail['client'],
  service: {
    id: 1,
    category_id: 1,
    name: 'Corte',
    duration_minutes: 60,
    price: 100,
    points_reward: 0,
    is_active: true,
  } as AppointmentDetail['service'],
}

describe('CompleteModal — fluxo de pagamento', () => {
  beforeEach(() => {
    completeMock.mockReset().mockResolvedValue({})
    uploadPhotosMock.mockReset().mockResolvedValue({})
  })

  it('envia paid=false por padrão quando o checkbox de pagamento não é marcado', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<CompleteModal appt={appt} onClose={() => {}} onSuccess={onSuccess} />)

    await user.click(screen.getByRole('button', { name: 'Concluir Atendimento' }))

    await waitFor(() => expect(completeMock).toHaveBeenCalledTimes(1))
    const body = completeMock.mock.calls[0][1]
    expect(body.paid).toBe(false)
  })

  it('bloqueia o envio (validação nativa required) se marcar "pago" sem escolher forma de pagamento', async () => {
    const user = userEvent.setup()
    render(<CompleteModal appt={appt} onClose={() => {}} onSuccess={() => {}} />)

    await user.click(screen.getByLabelText('Pagamento recebido'))
    const paymentMethodSelect = screen.getByLabelText('Forma de pagamento *') as HTMLSelectElement
    expect(paymentMethodSelect).toBeRequired()

    await user.click(screen.getByRole('button', { name: 'Concluir Atendimento' }))

    expect(completeMock).not.toHaveBeenCalled()
  })

  it('envia paid=true com amount_paid e payment_method quando preenchidos', async () => {
    const user = userEvent.setup()
    const onSuccess = vi.fn()
    render(<CompleteModal appt={appt} onClose={() => {}} onSuccess={onSuccess} />)

    await user.click(screen.getByLabelText('Pagamento recebido'))
    await user.selectOptions(screen.getByLabelText('Forma de pagamento *'), 'pix')
    await user.clear(screen.getByLabelText('Valor recebido (R$) *'))
    await user.type(screen.getByLabelText('Valor recebido (R$) *'), '100')
    await user.click(screen.getByRole('button', { name: 'Concluir Atendimento' }))

    await waitFor(() => expect(completeMock).toHaveBeenCalledTimes(1))
    const body = completeMock.mock.calls[0][1]
    expect(body.paid).toBe(true)
    expect(body.payment_method).toBe('pix')
    expect(onSuccess).toHaveBeenCalled()
  })

  it('falha de upload não conclui nem cobra o atendimento; permite nova tentativa', async () => {
    const user = userEvent.setup()
    uploadPhotosMock.mockRejectedValueOnce(new Error('upload failed'))
    const onSuccess = vi.fn()
    render(<CompleteModal appt={appt} onClose={() => {}} onSuccess={onSuccess} />)
    await user.upload(screen.getByLabelText('Foto antes'), new File(['image'], 'antes.jpg', { type: 'image/jpeg' }))
    await user.click(screen.getByRole('button', { name: 'Concluir Atendimento' }))
    await screen.findByText('Erro ao concluir atendimento.')
    expect(completeMock).not.toHaveBeenCalled()
    expect(onSuccess).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Concluir Atendimento' }))
    await waitFor(() => expect(onSuccess).toHaveBeenCalledOnce())
    expect(completeMock).toHaveBeenCalledOnce()
  })
})
