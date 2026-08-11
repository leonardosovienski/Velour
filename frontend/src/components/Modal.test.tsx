import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Modal } from './Modal'

describe('Modal', () => {
  it('não renderiza nada quando open=false', () => {
    render(<Modal title="Teste" open={false} onClose={() => {}}>conteúdo</Modal>)
    expect(screen.queryByText('conteúdo')).not.toBeInTheDocument()
  })

  it('renderiza título e conteúdo quando open=true', () => {
    render(<Modal title="Concluir Atendimento" open={true} onClose={() => {}}>conteúdo do modal</Modal>)
    expect(screen.getByText('Concluir Atendimento')).toBeInTheDocument()
    expect(screen.getByText('conteúdo do modal')).toBeInTheDocument()
  })

  it('chama onClose ao clicar no botão de fechar', () => {
    const onClose = vi.fn()
    render(<Modal title="Teste" open={true} onClose={onClose}>x</Modal>)
    fireEvent.click(screen.getByRole('button'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('chama onClose ao pressionar Escape', () => {
    const onClose = vi.fn()
    render(<Modal title="Teste" open={true} onClose={onClose}>x</Modal>)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
