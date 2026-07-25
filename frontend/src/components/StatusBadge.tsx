import type { AppointmentStatus } from '../api/types'

const config: Record<AppointmentStatus, { label: string; className: string }> = {
  scheduled:   { label: 'Agendado',      className: 'bg-sky-900/30 text-sky-400 border-sky-800/40' },
  confirmed:   { label: 'Confirmado',    className: 'bg-blue-900/30 text-blue-400 border-blue-800/40' },
  in_progress: { label: 'Em atendimento', className: 'bg-purple-900/30 text-purple-400 border-purple-800/40' },
  completed:   { label: 'Concluído',     className: 'bg-success/20 text-green-400 border-success/40' },
  cancelled:   { label: 'Cancelado',     className: 'bg-danger/20 text-red-400 border-danger/40' },
  no_show:     { label: 'Não compareceu', className: 'bg-gray-800/40 text-muted border-border' },
}

export function StatusBadge({ status }: { status: AppointmentStatus }) {
  const { label, className } = config[status] ?? { label: status, className: 'bg-border text-muted border-border' }
  return (
    <span className={`inline-flex items-center border rounded-full text-[10px] font-medium px-2.5 py-1 ${className}`}>
      {label}
    </span>
  )
}
