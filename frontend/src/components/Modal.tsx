import { type ReactNode, useEffect, useId, useRef } from 'react'
import { X } from 'lucide-react'

interface Props {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
  width?: string
}

export function Modal({ title, open, onClose, children, width = 'max-w-lg' }: Props) {
  const titleId = useId()
  const triggerRef = useRef<Element | null>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  useEffect(() => {
    if (open) {
      triggerRef.current = document.activeElement
    } else if (triggerRef.current instanceof HTMLElement) {
      triggerRef.current.focus()
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative bg-surface border border-border rounded-xl w-full ${width} max-h-[90vh] overflow-y-auto shadow-2xl`}>
        <div className="flex items-center justify-between p-5 border-b border-border">
          <h2 id={titleId} className="font-display text-xl font-semibold text-cream">{title}</h2>
          <button onClick={onClose} aria-label="Fechar" className="text-muted hover:text-cream transition-colors p-1">
            <X size={18} />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}
