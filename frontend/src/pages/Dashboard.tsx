import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { Calendar, TrendingUp, Users, Star, Cake, Crown, BookOpen, AlertTriangle, CalendarClock } from 'lucide-react'
import { dashboardApi } from '../api/client'
import type { DashboardToday, DashboardKPIs, WeeklyRevenueItem, DashboardAlerts } from '../api/types'
import { Layout, Card } from '../components/Layout'
import { TierBadge } from '../components/TierBadge'
import { StatusBadge } from '../components/StatusBadge'
import { BriefingDrawer } from '../components/BriefingDrawer'
import { PageSpinner } from '../components/Spinner'
import { useAuth } from '../context/AuthContext'

const statusOrder = ['scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']

export function Dashboard() {
  const { user } = useAuth()
  const [today, setToday] = useState<DashboardToday | null>(null)
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null)
  const [weekly, setWeekly] = useState<WeeklyRevenueItem[]>([])
  const [alerts, setAlerts] = useState<DashboardAlerts | null>(null)
  const [loading, setLoading] = useState(true)
  const [briefingClientId, setBriefingClientId] = useState<number | null>(null)

  useEffect(() => {
    Promise.all([
      dashboardApi.today(),
      dashboardApi.kpis('day'),
      dashboardApi.weeklyRevenue(),
      dashboardApi.alerts(),
    ]).then(([t, k, w, a]) => {
      setToday(t)
      setKpis(k)
      setWeekly(w)
      setAlerts(a)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Layout><PageSpinner /></Layout>

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite'
  const todayLabel = format(new Date(), "EEEE, d 'de' MMMM yyyy", { locale: ptBR })

  const maxRevenue = Math.max(...weekly.map(w => w.revenue), 1)

  return (
    <Layout>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl font-semibold text-cream">
            {greeting}, {user?.name.split(' ')[0]}.
          </h1>
          <p className="text-muted text-sm mt-1 capitalize">{todayLabel}</p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          icon={<Calendar size={18} className="text-blue-400" />}
          label="Agendamentos hoje"
          value={String(today?.total_appointments ?? 0)}
          bg="bg-blue-900/20 border-blue-800/30"
        />
        <KpiCard
          icon={<TrendingUp size={18} className="text-green-400" />}
          label="Receita hoje"
          value={`R$${(today?.revenue_today ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`}
          bg="bg-success/10 border-success/30"
        />
        <KpiCard
          icon={<Users size={18} className="text-purple-400" />}
          label="Clientes ativos"
          value={String(kpis?.active_clients ?? 0)}
          bg="bg-purple-900/20 border-purple-800/30"
        />
        <KpiCard
          icon={<Star size={18} className="text-gold" />}
          label="Pontos emitidos hoje"
          value={(kpis?.points_issued ?? 0).toLocaleString('pt-BR')}
          bg="bg-gold/10 border-gold/20"
        />
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Weekly Revenue Chart */}
        <div className="col-span-2">
          <Card>
            <div className="text-muted text-xs uppercase tracking-widest mb-4 flex items-center gap-2">
              <TrendingUp size={12} /> Receita — últimos 7 dias
            </div>
            <div className="flex items-end gap-3 h-36">
              {weekly.map(day => (
                <div key={day.date} className="flex-1 flex flex-col items-center gap-1.5">
                  <div className="text-gold/80 text-xs font-mono">
                    {day.revenue > 0 ? `R$${Math.round(day.revenue)}` : ''}
                  </div>
                  <div className="w-full rounded-t-md bg-gold/20 hover:bg-gold/40 transition-colors relative group"
                    style={{ height: `${Math.max(4, (day.revenue / maxRevenue) * 96)}px` }}
                    title={`${day.appointments} atend.`}
                  >
                    <div className="w-full rounded-t-md bg-gold transition-all"
                      style={{ height: `${Math.max(4, (day.revenue / maxRevenue) * 96)}px` }}
                    />
                  </div>
                  <div className="text-muted text-[10px]">{day.date}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Alerts */}
        <Card className="flex flex-col gap-4">
          <div className="text-muted text-xs uppercase tracking-widest">Alertas do dia</div>
          {alerts?.birthdays_today && alerts.birthdays_today.length > 0 ? (
            <div>
              <div className="flex items-center gap-2 text-pink-400 text-xs font-semibold mb-2">
                <Cake size={13} /> Aniversariantes ({alerts.birthdays_today.length})
              </div>
              <div className="space-y-1.5">
                {alerts.birthdays_today.map(c => (
                  <div key={c.id} className="text-sm text-cream">
                    {c.name} <span className="text-muted font-mono text-xs">{c.code}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-muted text-xs">
              <Cake size={13} /> Nenhum aniversário hoje
            </div>
          )}

          <div className="border-t border-border pt-4">
            {alerts?.platinum_today && alerts.platinum_today.length > 0 ? (
              <div>
                <div className="flex items-center gap-2 text-violet-400 text-xs font-semibold mb-2">
                  <Crown size={13} /> Platinum agendados ({alerts.platinum_today.length})
                </div>
                <div className="space-y-1.5">
                  {alerts.platinum_today.map(p => (
                    <div key={p.appointment_id} className="text-sm text-cream">
                      {p.client_name}
                      <div className="text-muted text-xs font-mono">
                        {format(new Date(p.scheduled_at), 'HH:mm')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-muted text-xs">
                <Crown size={13} /> Nenhum cliente Platinum hoje
              </div>
            )}
          </div>

          {(alerts?.low_stock?.length || alerts?.expiring_soon?.length) ? (
            <div className="border-t border-border pt-4 space-y-3">
              {alerts?.low_stock?.length ? (
                <div>
                  <div className="flex items-center gap-2 text-danger text-xs font-semibold mb-2">
                    <AlertTriangle size={13} /> Estoque baixo ({alerts.low_stock.length})
                  </div>
                  <div className="space-y-1.5">
                    {alerts.low_stock.map(p => (
                      <div key={p.id} className="text-sm text-cream flex justify-between gap-2">
                        <span className="truncate">{p.name}</span>
                        <span className="font-mono text-xs text-danger flex-shrink-0">{p.stock_qty} / {p.min_stock} {p.unit}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              {alerts?.expiring_soon?.length ? (
                <div>
                  <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold mb-2">
                    <CalendarClock size={13} /> Vencendo em breve ({alerts.expiring_soon.length})
                  </div>
                  <div className="space-y-1.5">
                    {alerts.expiring_soon.map(p => (
                      <div key={p.id} className="text-sm text-cream flex justify-between gap-2">
                        <span className="truncate">{p.name}</span>
                        <span className="font-mono text-xs text-amber-400 flex-shrink-0">
                          {p.days_to_expiry < 0 ? 'vencido' : `${p.days_to_expiry}d`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </Card>
      </div>

      {/* Status Breakdown */}
      {today?.status_breakdown && (
        <div className="grid grid-cols-6 gap-3 mb-6">
          {statusOrder.map(status => {
            const count = today.status_breakdown[status] ?? 0
            return (
              <div key={status} className="bg-surface border border-border rounded-lg p-3 text-center">
                <div className="font-mono text-xl text-cream">{count}</div>
                <StatusBadge status={status as any} />
              </div>
            )
          })}
        </div>
      )}

      {/* Today's Appointments */}
      <Card>
        <div className="text-muted text-xs uppercase tracking-widest mb-4">
          Agendamentos de hoje ({today?.appointments.length ?? 0})
        </div>
        {!today?.appointments.length ? (
          <div className="text-center py-10 text-muted text-sm">Nenhum agendamento para hoje.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-muted text-xs uppercase tracking-wider">
                  <th className="text-left pb-3 pr-4">Horário</th>
                  <th className="text-left pb-3 pr-4">Cliente</th>
                  <th className="text-left pb-3 pr-4">Profissional</th>
                  <th className="text-left pb-3 pr-4">Serviço</th>
                  <th className="text-left pb-3 pr-4">Status</th>
                  <th className="text-left pb-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {today.appointments.map(appt => (
                  <tr key={appt.id} className="hover:bg-white/2 transition-colors">
                    <td className="py-3 pr-4 font-mono text-gold">
                      {format(new Date(appt.scheduled_at), 'HH:mm')}
                      <span className="text-muted text-xs block">
                        até {format(new Date(appt.ends_at), 'HH:mm')}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="text-cream font-medium">{appt.client.name}</div>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className="font-mono text-muted text-xs">{appt.client.code}</span>
                        <TierBadge tier={appt.client.tier} size="xs" />
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-cream">{appt.professional.name}</td>
                    <td className="py-3 pr-4 text-cream">
                      {appt.service.name}
                      <span className="text-muted text-xs block">{appt.service.duration_minutes} min</span>
                    </td>
                    <td className="py-3 pr-4">
                      <StatusBadge status={appt.status} />
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => setBriefingClientId(appt.client.id)}
                        className="flex items-center gap-1.5 text-xs text-muted hover:text-gold transition-colors border border-border hover:border-gold/40 rounded-md px-2.5 py-1.5"
                      >
                        <BookOpen size={12} /> Briefing
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <BriefingDrawer clientId={briefingClientId} onClose={() => setBriefingClientId(null)} />
    </Layout>
  )
}

function KpiCard({ icon, label, value, bg }: { icon: React.ReactNode; label: string; value: string; bg: string }) {
  return (
    <div className={`bg-surface border rounded-xl p-5 ${bg}`}>
      <div className="flex items-center gap-2 mb-3">{icon}<span className="text-xs text-muted">{label}</span></div>
      <div className="font-mono text-2xl font-medium text-cream">{value}</div>
    </div>
  )
}
