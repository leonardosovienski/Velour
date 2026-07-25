import { useEffect, useState, type ReactNode } from 'react'
import { X, Coffee, Music, Thermometer, MessageCircle, AlertTriangle, Star, TrendingUp } from 'lucide-react'
import { clientsApi } from '../api/client'
import type { ClientBriefing } from '../api/types'
import { TierBadge } from './TierBadge'
import { Spinner } from './Spinner'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

const chatLabels: Record<string, string> = {
  quiet: 'Prefere silêncio',
  neutral: 'Neutro',
  chatty: 'Gosta de conversar',
}

const tierMax: Record<string, number> = {
  bronze: 500, silver: 1500, gold: 3000, platinum: Infinity,
}

interface Props {
  clientId: number | null
  onClose: () => void
}

export function BriefingDrawer({ clientId, onClose }: Props) {
  const [briefing, setBriefing] = useState<ClientBriefing | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!clientId) { setBriefing(null); return }
    setLoading(true)
    clientsApi.briefing(clientId)
      .then(setBriefing)
      .finally(() => setLoading(false))
  }, [clientId])

  useEffect(() => {
    if (!clientId) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [clientId, onClose])

  const open = !!clientId

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={onClose} />}
      <div className={`fixed top-0 right-0 h-full z-50 w-96 bg-surface border-l border-border shadow-2xl flex flex-col transition-transform duration-300 ${open ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="flex items-center justify-between p-5 border-b border-border flex-shrink-0">
          <span className="font-display text-lg font-semibold text-gold">Briefing do Cliente</span>
          <button onClick={onClose} className="text-muted hover:text-cream transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading && <div className="flex items-center justify-center h-40"><Spinner /></div>}
          {!loading && briefing && <BriefingContent briefing={briefing} />}
          {!loading && !briefing && clientId && (
            <p className="text-muted text-sm p-6">Erro ao carregar briefing.</p>
          )}
        </div>
      </div>
    </>
  )
}

function BriefingContent({ briefing }: { briefing: ClientBriefing }) {
  const tierLimit = tierMax[briefing.loyalty_tier] ?? Infinity
  const progress = tierLimit === Infinity ? 100 : Math.min(100, (briefing.total_spent / tierLimit) * 100)

  return (
    <div className="p-5 space-y-5">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
          <span className="font-display text-lg text-gold font-semibold">
            {briefing.name.charAt(0).toUpperCase()}
          </span>
        </div>
        <div>
          <div className="font-display text-lg font-semibold text-cream">{briefing.name}</div>
          <div className="text-muted text-xs font-mono">{briefing.code}</div>
          <div className="mt-1"><TierBadge tier={briefing.loyalty_tier} /></div>
        </div>
      </div>

      {/* Loyalty */}
      <div className="bg-bg rounded-lg p-4 border border-border space-y-2">
        <div className="flex items-center gap-1.5 text-gold text-xs font-semibold uppercase tracking-widest mb-3">
          <Star size={12} /> Fidelidade
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          <Stat label="Pontos" value={briefing.loyalty_points.toLocaleString('pt-BR')} />
          <Stat label="Visitas" value={String(briefing.total_visits)} />
          <Stat label="Gasto total" value={`R$${briefing.total_spent.toLocaleString('pt-BR', { minimumFractionDigits: 0 })}`} />
        </div>
        {briefing.loyalty_tier !== 'platinum' && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-muted mb-1">
              <span>Progresso para o próximo tier</span>
              {briefing.spent_to_next_tier && (
                <span>faltam R${briefing.spent_to_next_tier.toLocaleString('pt-BR', { minimumFractionDigits: 0 })}</span>
              )}
            </div>
            <div className="h-1.5 bg-border rounded-full overflow-hidden">
              <div className="h-full bg-gold rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Sensory Profile */}
      <div className="space-y-2">
        <div className="text-muted text-xs font-semibold uppercase tracking-widest mb-3">Perfil Sensorial</div>
        <div className="space-y-2">
          {briefing.preferred_drink && (
            <SensoryRow icon={<Coffee size={14} />} label="Bebida" value={briefing.preferred_drink} />
          )}
          {briefing.music_preference && (
            <SensoryRow icon={<Music size={14} />} label="Música" value={briefing.music_preference} />
          )}
          {briefing.temperature_preference && (
            <SensoryRow icon={<Thermometer size={14} />} label="Temperatura" value={briefing.temperature_preference} />
          )}
          <SensoryRow icon={<MessageCircle size={14} />} label="Conversa" value={chatLabels[briefing.chat_preference] ?? briefing.chat_preference} />
        </div>
      </div>

      {/* Allergies */}
      {briefing.allergies && (
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-3">
          <div className="flex items-center gap-2 text-red-400 text-xs font-semibold mb-1">
            <AlertTriangle size={13} /> Alergias / Restrições
          </div>
          <p className="text-cream text-sm">{briefing.allergies}</p>
        </div>
      )}

      {/* Notes */}
      {briefing.notes && (
        <div className="bg-bg rounded-lg p-3 border border-border">
          <div className="text-muted text-xs font-semibold mb-1">Observações</div>
          <p className="text-cream text-sm">{briefing.notes}</p>
        </div>
      )}

      {/* Last Appointment */}
      {briefing.last_appointment && (
        <div className="bg-bg rounded-lg p-4 border border-border">
          <div className="flex items-center gap-1.5 text-muted text-xs font-semibold uppercase tracking-widest mb-3">
            <TrendingUp size={12} /> Último Atendimento
          </div>
          <div className="space-y-1 text-sm">
            <div className="text-cream font-medium">{briefing.last_appointment.service_name}</div>
            <div className="text-muted text-xs">
              {briefing.last_appointment.professional_name} &middot;{' '}
              {format(new Date(briefing.last_appointment.date), "dd 'de' MMM yyyy", { locale: ptBR })}
            </div>
            {briefing.last_appointment.formula_used && (
              <div className="mt-2 bg-surface rounded p-2 font-mono text-xs text-gold/80">
                {briefing.last_appointment.formula_used}
              </div>
            )}
            {briefing.last_appointment.notes && (
              <p className="text-muted text-xs mt-1">{briefing.last_appointment.notes}</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-sm font-medium text-cream">{value}</div>
      <div className="text-muted text-xs">{label}</div>
    </div>
  )
}

function SensoryRow({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-border last:border-0">
      <span className="text-gold flex-shrink-0">{icon}</span>
      <span className="text-muted text-xs w-20">{label}</span>
      <span className="text-cream text-sm">{value}</span>
    </div>
  )
}
