import { type ReactNode, useState } from 'react'
import { Menu } from 'lucide-react'
import { Sidebar } from './Sidebar'

export function Layout({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-bg overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — fixed drawer on mobile, static on desktop */}
      <div className={`
        fixed md:relative inset-y-0 left-0 z-30 h-full
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        md:translate-x-0 md:flex-shrink-0
      `}>
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      <main className="flex-1 overflow-y-auto min-w-0">
        {/* Mobile top bar */}
        <div className="md:hidden sticky top-0 z-10 flex items-center gap-3 px-4 py-3 bg-surface border-b border-border">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-muted hover:text-cream p-1"
            aria-label="Abrir menu"
          >
            <Menu size={20} />
          </button>
          <span className="font-display text-lg font-semibold text-gold tracking-wide">VELOUR</span>
        </div>

        <div className="max-w-6xl mx-auto p-4 md:p-8">
          {children}
        </div>
      </main>
    </div>
  )
}

export function PageHeader({ title, subtitle, action }: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="flex items-start justify-between mb-8">
      <div>
        <h1 className="font-display text-3xl font-semibold text-cream">{title}</h1>
        {subtitle && <p className="text-muted text-sm mt-1">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-surface border border-border rounded-xl p-5 ${className}`}>
      {children}
    </div>
  )
}
