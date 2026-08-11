import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it('mostra o rótulo em português para cada status conhecido', () => {
    render(<StatusBadge status="completed" />)
    expect(screen.getByText('Concluído')).toBeInTheDocument()
  })

  it('mostra o rótulo de cancelado', () => {
    render(<StatusBadge status="cancelled" />)
    expect(screen.getByText('Cancelado')).toBeInTheDocument()
  })
})
