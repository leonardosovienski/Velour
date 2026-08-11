import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ErrorBoundary } from './ErrorBoundary'

function Boom(): never {
  throw new Error('falha proposital')
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renderiza os filhos normalmente quando não há erro', () => {
    render(<ErrorBoundary><div>conteúdo normal</div></ErrorBoundary>)
    expect(screen.getByText('conteúdo normal')).toBeInTheDocument()
  })

  it('mostra a UI de fallback quando um filho lança erro', () => {
    render(<ErrorBoundary><Boom /></ErrorBoundary>)
    expect(screen.getByText('Algo deu errado')).toBeInTheDocument()
  })
})
