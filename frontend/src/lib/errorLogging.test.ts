import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { logError } from './errorLogging'

describe('logError', () => {
  let spy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    spy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })
  afterEach(() => {
    spy.mockRestore()
  })

  it('emite log estruturado em JSON com mensagem e contexto', () => {
    logError(new Error('deu ruim'), 'meu-contexto')
    expect(spy).toHaveBeenCalledTimes(1)
    const payload = JSON.parse(spy.mock.calls[0][0] as string)
    expect(payload.message).toBe('deu ruim')
    expect(payload.context).toBe('meu-contexto')
    expect(payload.timestamp).toBeDefined()
  })

  it('converte valores não-Error em Error', () => {
    logError('string qualquer')
    const payload = JSON.parse(spy.mock.calls[0][0] as string)
    expect(payload.message).toBe('string qualquer')
  })
})
