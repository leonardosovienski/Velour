import { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import api, { authApi, billingApi, photosApi, getErrorDetail } from './client'

const originalAdapter = api.defaults.adapter
function rejectWith(status: number) {
  api.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
    throw new AxiosError('request failed', undefined, config, undefined, { data: { detail: 'error' }, status, statusText: 'Error', headers: {}, config })
  }
}
beforeEach(() => { sessionStorage.clear(); vi.restoreAllMocks() })
afterEach(() => { api.defaults.adapter = originalAdapter })

describe('HTTP session handling', () => {
  it('401 no login permite apresentar erro sem encerrar ou recarregar a sessão', async () => {
    sessionStorage.setItem('access_token', 'existing-token')
    const listener = vi.fn(); window.addEventListener('velour:session-expired', listener)
    rejectWith(401)
    await expect(authApi.login('ana@example.com', 'wrong')).rejects.toBeInstanceOf(AxiosError)
    expect(listener).not.toHaveBeenCalled()
    expect(sessionStorage.getItem('access_token')).toBe('existing-token')
    window.removeEventListener('velour:session-expired', listener)
  })
  it('401 em rota autenticada remove credencial e comunica expiração', async () => {
    sessionStorage.setItem('access_token', 'expired-token')
    const listener = vi.fn(); window.addEventListener('velour:session-expired', listener)
    rejectWith(401)
    await expect(authApi.me()).rejects.toBeInstanceOf(AxiosError)
    expect(listener).toHaveBeenCalledOnce()
    expect(sessionStorage.getItem('access_token')).toBeNull()
    window.removeEventListener('velour:session-expired', listener)
  })
  it('402 pede regularização mantendo sessão para acessar cobrança e exportação', async () => {
    sessionStorage.setItem('access_token', 'valid-token')
    const listener = vi.fn(); window.addEventListener('velour:subscription-required', listener)
    rejectWith(402)
    await expect(billingApi.status()).rejects.toBeInstanceOf(AxiosError)
    expect(listener).toHaveBeenCalledOnce()
    expect(sessionStorage.getItem('access_token')).toBe('valid-token')
    window.removeEventListener('velour:subscription-required', listener)
  })
  it('carrega foto com Bearer e rejeita destinos externos antes de enviar credenciais', async () => {
    sessionStorage.setItem('access_token', 'private-token')
    const adapter = vi.fn(async (config: InternalAxiosRequestConfig) => ({ data: new Blob(['image']), status: 200, statusText: 'OK', headers: {}, config }))
    api.defaults.adapter = adapter
    await photosApi.get('/uploads/abcd1234.jpg')
    expect(adapter.mock.calls[0][0].headers.Authorization).toBe('Bearer private-token')
    await expect(photosApi.get('https://external.example.com/photo.jpg')).rejects.toThrow('Invalid photo path')
    expect(adapter).toHaveBeenCalledOnce()
  })
  it('não entrega objetos de validação à renderização de texto React', async () => {
    api.defaults.adapter = async config => { throw new AxiosError('invalid', undefined, config, undefined, { data: { detail: [{ msg: 'Invalid input', input: 'sensitive-value' }] }, status: 422, statusText: '', headers: {}, config }) }
    try { await authApi.me() } catch (error) { expect(getErrorDetail(error)).toBe('Verifique os campos informados e tente novamente.') }
  })
})
