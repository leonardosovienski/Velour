import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { ArrowLeft, Phone, Mail, Coffee, Music, Thermometer, MessageCircle, AlertTriangle, Star, Calendar } from 'lucide-react'
import { clientsApi, loyaltyApi, appointmentsApi } from '../api/client'
import type { ClientResponse, LoyaltyTransactionResponse, AppointmentDetail } from '../api/types'
import { Layout, Card } from '../components/Layout'
import { TierBadge } from '../components/TierBadge'
import { StatusBadge } from '../components/StatusBadge'
import { PageSpinner } from '../components/Spinner'

const tierMax: Record<string, number> = {
  bronze: 500, silver: 1500, gold: 3000, platinum: Infinity,
}

export function ClientProfile() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [client, setClient] = useState<ClientResponse | null>(null)
  const [appointments, setAppointments] = useState<AppointmentDetail[]>([])
  const [txs, setTxs] = useState<LoyaltyTransactionResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    const nid = Number(id)
    Promise.all([
      clientsApi.get(nid),
      appointmentsApi.list({ client_id: nid, limit: 20 }),
      loyaltyApi.transactions({ client_id: nid, limit: 20 }),
    ]).then(([c, a, t]) => {
      setClient(c)
      setAppointments(a)
      setTxs(t)
    }).finally(() => setLoading(false))
  }, [id])

  if (loading) return <Layout><PageSpinner /></Layout>
  if (!client) return <Layout><div className="text-muted">Cliente não encontrado.</div></Layout>

  const tierLimit = tierMax[client.loyalty_tier] ?? Infinity
  const progress = tierLimit === Infinity ? 100 : Math.min(100, (client.total_spent / tierLimit) * 100)
  const nextTier = { bronze: 'Silver', silver: 'Gold', gold: 'Platinum', platinum: null }[client.loyalty_tier]

  return (
    <Layout>
      <button onClick={() => navigate('/clients')} className="flex items-center gap-2 text-muted hover:text-cream text-sm mb-6 transition-colors">
        <ArrowLeft size={14} /> Voltar para Clientes
      </button>

      {/* Header */}
      <div className="flex items-start gap-5 mb-8">
        <div className="w-16 h-16 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
          <span className="font-display text-2xl text-gold font-semibold">{client.name.charAt(0)}</span>
        </div>
        <div className="flex-1">
          <div className="flex items-start gap-3 flex-wrap">
            <h1 className="font-display text-3xl font-semibold text-cream">{client.name}</h1>
            <TierBadge tier={client.loyalty_tier} />
          </div>
          <div className="text-muted font-mono text-sm">{client.code}</div>
          <div className="flex items-center gap-4 mt-2 text-sm text-muted">
            {client.phone && <span className="flex items-center gap-1"><Phone size={12} /> {client.phone}</span>}
            {client.email && <span className="flex items-center gap-1"><Mail size={12} /> {client.email}</span>}
            <span>Desde {format(new Date(client.first_visit), "MMM yyyy", { locale: ptBR })}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left column */}
        <div className="space-y-5">
          {/* Loyalty */}
          <Card>
            <div className="flex items-center gap-2 text-gold text-xs font-semibold uppercase tracking-widest mb-4">
              <Star size={12} /> Fidelidade
            </div>
            <div className="grid grid-cols-3 gap-3 text-center mb-4">
              <div>
                <div className="font-mono text-xl text-cream">{client.loyalty_points.toLocaleString('pt-BR')}</div>
                <div className="text-muted text-xs">Pontos</div>
              </div>
              <div>
                <div className="font-mono text-xl text-cream">{client.total_visits}</div>
                <div className="text-muted text-xs">Visitas</div>
              </div>
              <div>
                <div className="font-mono text-xl text-cream">R${Math.round(client.total_spent / Math.max(1, client.total_visits))}</div>
                <div className="text-muted text-xs">Ticket médio</div>
              </div>
            </div>
            <div className="text-xs text-muted font-mono mb-2">
              Total gasto: R${client.total_spent.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </div>
            {nextTier && (
              <>
                <div className="flex justify-between text-xs text-muted mb-1">
                  <span>Progresso → {nextTier}</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-1.5 bg-border rounded-full overflow-hidden">
                  <div className="h-full bg-gold rounded-full" style={{ width: `${progress}%` }} />
                </div>
              </>
            )}
          </Card>

          {/* Sensory Profile */}
          <Card>
            <div className="text-muted text-xs font-semibold uppercase tracking-widest mb-4">Perfil Sensorial</div>
            <div className="space-y-3">
              {client.preferred_drink && <SensoryRow icon={<Coffee size={14} />} label="Bebida" value={client.preferred_drink} />}
              {client.music_preference && <SensoryRow icon={<Music size={14} />} label="Música" value={client.music_preference} />}
              {client.temperature_preference && <SensoryRow icon={<Thermometer size={14} />} label="Temperatura" value={client.temperature_preference} />}
              <SensoryRow icon={<MessageCircle size={14} />} label="Conversa" value={{ quiet: 'Prefere silêncio', neutral: 'Neutro', chatty: 'Gosta de conversar' }[client.chat_preference] ?? client.chat_preference} />
            </div>
          </Card>

          {/* Allergies */}
          {client.allergies && (
            <div className="bg-danger/10 border border-danger/30 rounded-xl p-4">
              <div className="flex items-center gap-2 text-red-400 text-xs font-semibold mb-2">
                <AlertTriangle size={13} /> Alergias / Restrições
              </div>
              <p className="text-cream text-sm">{client.allergies}</p>
            </div>
          )}

          {/* Notes */}
          {client.notes && (
            <Card>
              <div className="text-muted text-xs font-semibold mb-2">Observações</div>
              <p className="text-cream text-sm">{client.notes}</p>
            </Card>
          )}

          {/* Referral */}
          <Card>
            <div className="text-muted text-xs font-semibold mb-2">Código de indicação</div>
            <div className="font-mono text-lg text-gold">{client.referral_code}</div>
            <div className="text-muted text-xs mt-1">Compartilhe com amigos para ganhar pontos</div>
          </Card>
        </div>

        {/* Right: 2 columns */}
        <div className="col-span-2 space-y-6">
          {/* Appointments */}
          <Card>
            <div className="flex items-center gap-2 text-muted text-xs font-semibold uppercase tracking-widest mb-4">
              <Calendar size={12} /> Histórico de Atendimentos ({appointments.length})
            </div>
            {!appointments.length ? (
              <div className="text-center py-8 text-muted text-sm">Nenhum atendimento registrado.</div>
            ) : (
              <div className="divide-y divide-border">
                {appointments.map(appt => (
                  <div key={appt.id} className="py-3 flex items-start justify-between">
                    <div>
                      <div className="text-cream text-sm font-medium">{appt.service?.name ?? `Serviço #${appt.service_id}`}</div>
                      <div className="text-muted text-xs mt-0.5">
                        {appt.professional?.name} &middot; {format(new Date(appt.scheduled_at), "dd MMM yyyy HH:mm", { locale: ptBR })}
                      </div>
                      {appt.formula_used && (
                        <div className="font-mono text-xs text-gold/70 mt-1 bg-bg rounded px-2 py-1 inline-block">
                          {appt.formula_used}
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <StatusBadge status={appt.status} />
                      {appt.price_charged != null && (
                        <div className="font-mono text-sm text-cream mt-1">
                          R${appt.price_charged.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </div>
                      )}
                      {appt.points_awarded > 0 && (
                        <div className="text-gold text-xs">+{appt.points_awarded} pts</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Loyalty Transactions */}
          <Card>
            <div className="flex items-center gap-2 text-muted text-xs font-semibold uppercase tracking-widest mb-4">
              <Star size={12} /> Histórico de Pontos ({txs.length})
            </div>
            {!txs.length ? (
              <div className="text-center py-8 text-muted text-sm">Nenhuma transação de pontos.</div>
            ) : (
              <div className="divide-y divide-border">
                {txs.map(tx => (
                  <div key={tx.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="text-cream text-sm">{tx.description}</div>
                      <div className="text-muted text-xs">{format(new Date(tx.created_at), "dd MMM yyyy", { locale: ptBR })}</div>
                    </div>
                    <div className={`font-mono text-sm font-semibold ${tx.type === 'redeemed' ? 'text-red-400' : 'text-green-400'}`}>
                      {tx.type === 'redeemed' ? '-' : '+'}{Math.abs(tx.points).toLocaleString('pt-BR')} pts
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </Layout>
  )
}

function SensoryRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-gold">{icon}</span>
      <span className="text-muted text-xs w-20">{label}</span>
      <span className="text-cream text-sm">{value}</span>
    </div>
  )
}
