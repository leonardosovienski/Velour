import type { ReactNode } from 'react'
import { Link } from 'react-router'

export function AuthShell({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <main className="min-h-dvh bg-bg flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <Link to="/login" aria-label="Velour, entrar" className="block text-center mb-8">
          <div className="font-display text-5xl font-semibold text-gold tracking-widest mb-2">VELOUR</div>
          <div className="text-muted text-xs uppercase tracking-[0.3em]">Gestão de salão</div>
        </Link>
        <div className="bg-surface border border-border rounded-2xl p-6 sm:p-8 shadow-2xl">
          <h1 className="font-display text-2xl text-cream font-medium">{title}</h1>
          {subtitle && <p className="text-muted text-sm mt-2 leading-relaxed">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </main>
  )
}

export function FormError({ message }: { message: string }) {
  return message ? <p role="alert" className="bg-danger/10 border border-danger/30 text-red-300 text-sm rounded-lg px-4 py-3">{message}</p> : null
}
