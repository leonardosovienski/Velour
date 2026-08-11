import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TierBadge } from './TierBadge'

describe('TierBadge', () => {
  it('mostra o nome do tier em maiúsculas via CSS uppercase e texto original', () => {
    render(<TierBadge tier="gold" />)
    expect(screen.getByText('Gold')).toBeInTheDocument()
  })

  it('aplica classes menores quando size=xs', () => {
    render(<TierBadge tier="platinum" size="xs" />)
    expect(screen.getByText('Platinum').className).toContain('text-[9px]')
  })
})
