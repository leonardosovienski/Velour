import { render, screen, fireEvent } from '@testing-library/react'
import { useState } from 'react'
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

  it('expõe role=dialog, aria-modal e aria-labelledby apontando para o título', () => {
    render(<Modal title="Concluir Atendimento" open={true} onClose={() => {}}>x</Modal>)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    const labelledBy = dialog.getAttribute('aria-labelledby')
    expect(document.getElementById(labelledBy!)).toHaveTextContent('Concluir Atendimento')
  })

  it('o botão de fechar tem aria-label acessível', () => {
    render(<Modal title="Teste" open={true} onClose={() => {}}>x</Modal>)
    expect(screen.getByRole('button', { name: 'Fechar' })).toBeInTheDocument()
  })

  it('devolve o foco ao elemento que abriu o modal quando ele fecha', () => {
    function Wrapper() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button onClick={() => setOpen(true)}>abrir</button>
          <Modal title="Teste" open={open} onClose={() => setOpen(false)}>x</Modal>
        </>
      )
    }
    render(<Wrapper />)
    const trigger = screen.getByText('abrir')
    trigger.focus()
    fireEvent.click(trigger)
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(trigger).toHaveFocus()
  })
})
