import { useEffect, useState } from 'react'
import { BarChart2, Users, Star, Share2 } from 'lucide-react'
import { reportsApi } from '../api/client'
import type { RevenueReport, ClientReport, LoyaltyMonthlyItem, ReferralMonthlyItem, LoyaltyTier } from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { PageSpinner } from '../components/Spinner'

export function Reports() {
  const [tab, setTab] = useState<'revenue' | 'clients' | 'loyalty' | 'referrals'>('revenue')
  const [revenue, setRevenue] = useState<RevenueReport | null>(null)
  const [clients, setClients] = useState<ClientReport | null>(null)
  const [loyalty, setLoyalty] = useState<LoyaltyMonthlyItem[]>([])
  const [referrals, setReferrals] = useState<ReferralMonthlyItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      reportsApi.revenue(),
      reportsApi.clients(),
      reportsApi.loyaltyMonthly(6),
      reportsApi.referralsMonthly(6),
    ]).then(([r, c, l, rf]) => {
      setRevenue(r)
      setClients(c)
      setLoyalty(l)
      setReferrals(rf)
    }).finally(() => setLoading(false))
  }, [])

  const tabs = [
    { id: 'revenue' as const, icon: <BarChart2 size={14} />, label: 'Receita' },
    { id: 'clients' as const, icon: <Users size={14} />, label: 'Clientes' },
    { id: 'loyalty' as const, icon: <Star size={14} />, label: 'Fidelidade' },
    { id: 'referrals' as const, icon: <Share2 size={14} />, label: 'Indicações' },
  ]

  return (
    <Layout>
      <PageHeader title="Relatórios" subtitle="Análise de desempenho do salão" />

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-surface rounded-lg border border-border w-fit mb-6">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t.id ? 'bg-gold/10 text-gold border border-gold/20' : 'text-muted hover:text-cream'}`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {loading ? <PageSpinner /> : (
        <>
          {tab === 'revenue' && revenue && <RevenueTab data={revenue} />}
          {tab === 'clients' && clients && <ClientsTab data={clients} />}
          {tab === 'loyalty' && <LoyaltyTab data={loyalty} />}
          {tab === 'referrals' && <ReferralsTab data={referrals} />}
        </>
      )}
    </Layout>
  )
}

function RevenueTab({ data }: { data: RevenueReport }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <div className="text-muted text-xs uppercase tracking-widest mb-2">Receita Total</div>
          <div className="font-mono text-3xl text-cream">R${data.total_revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</div>
        </Card>
        <Card>
          <div className="text-muted text-xs uppercase tracking-widest mb-2">Atendimentos Concluídos</div>
          <div className="font-mono text-3xl text-cream">{data.total_appointments}</div>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <div className="text-muted text-xs uppercase tracking-widest mb-4">Por Profissional</div>
          <div className="divide-y divide-border">
            {data.by_professional.map(p => (
              <div key={p.name} className="py-3">
                <div className="flex justify-between mb-1">
                  <span className="text-cream text-sm">{p.name}</span>
                  <span className="font-mono text-sm text-gold">R${Math.round(p.revenue)}</span>
                </div>
                <div className="text-muted text-xs">{p.appointments} atend.</div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <div className="text-muted text-xs uppercase tracking-widest mb-4">Por Categoria</div>
          <div className="divide-y divide-border">
            {data.by_category.map(c => (
              <div key={c.name} className="py-3">
                <div className="flex justify-between mb-1">
                  <span className="text-cream text-sm">{c.name}</span>
                  <span className="font-mono text-sm text-gold">R${Math.round(c.revenue)}</span>
                </div>
                <div className="text-muted text-xs">{c.appointments} atend.</div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <div className="text-muted text-xs uppercase tracking-widest mb-4">Por Gênero</div>
          <div className="divide-y divide-border">
            {data.by_gender.map(g => (
              <div key={g.gender} className="py-3">
                <div className="flex justify-between mb-1">
                  <span className="text-cream text-sm capitalize">{g.gender}</span>
                  <span className="font-mono text-sm text-gold">R${Math.round(g.revenue)}</span>
                </div>
                <div className="text-muted text-xs">{g.appointments} atend.</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

function ClientsTab({ data }: { data: ClientReport }) {
  const tiers: LoyaltyTier[] = ['platinum', 'gold', 'silver', 'bronze']
  const tierColors: Record<LoyaltyTier, string> = {
    platinum: 'bg-violet-400', gold: 'bg-gold', silver: 'bg-slate-400', bronze: 'bg-amber-600',
  }
  const total = data.total_active

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <Card><Stat label="Clientes Ativos" value={String(data.total_active)} /></Card>
        <Card className="bg-success/5 border-success/20"><Stat label="Novos no Período" value={String(data.new_clients)} color="text-green-400" /></Card>
        <Card className="bg-danger/5 border-danger/20"><Stat label="Risco de Churn (60d)" value={String(data.churn_risk_count)} color="text-red-400" /></Card>
      </div>

      <Card>
        <div className="text-muted text-xs uppercase tracking-widest mb-4">Distribuição por Tier</div>
        <div className="space-y-4">
          {tiers.map(tier => {
            const count = data.tier_distribution[tier] ?? 0
            const pct = total > 0 ? (count / total) * 100 : 0
            return (
              <div key={tier}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="capitalize text-cream">{tier}</span>
                  <span className="font-mono text-muted">{count} ({pct.toFixed(0)}%)</span>
                </div>
                <div className="h-2 bg-border rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${tierColors[tier]}`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}

function LoyaltyTab({ data }: { data: LoyaltyMonthlyItem[] }) {
  const max = Math.max(...data.map(d => d.points_issued), 1)
  return (
    <Card>
      <div className="text-muted text-xs uppercase tracking-widest mb-6">Pontos — últimos 6 meses</div>
      <div className="space-y-4">
        {data.map(d => (
          <div key={d.month}>
            <div className="flex justify-between text-sm mb-1.5">
              <span className="text-cream">{d.month}</span>
              <span className="text-muted font-mono">{d.points_issued.toLocaleString('pt-BR')} emitidos / {d.points_redeemed.toLocaleString('pt-BR')} resgatados</span>
            </div>
            <div className="flex gap-1 h-2">
              <div className="h-full rounded-full bg-gold" style={{ width: `${(d.points_issued / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

function ReferralsTab({ data }: { data: ReferralMonthlyItem[] }) {
  return (
    <Card>
      <div className="text-muted text-xs uppercase tracking-widest mb-4">Indicações — últimos 6 meses</div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-muted text-xs uppercase tracking-wider">
            <th className="text-left pb-3 pr-4">Mês</th>
            <th className="text-left pb-3 pr-4">Criadas</th>
            <th className="text-left pb-3 pr-4">Convertidas</th>
            <th className="text-left pb-3 pr-4">Taxa</th>
            <th className="text-left pb-3">Pts investidos</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {data.map(d => (
            <tr key={d.month} className="hover:bg-white/2">
              <td className="py-3 pr-4 text-cream">{d.month}</td>
              <td className="py-3 pr-4 font-mono text-cream">{d.referrals_created}</td>
              <td className="py-3 pr-4 font-mono text-green-400">{d.referrals_converted}</td>
              <td className="py-3 pr-4 font-mono text-gold">{(d.conversion_rate * 100).toFixed(0)}%</td>
              <td className="py-3 font-mono text-muted">{d.points_invested.toLocaleString('pt-BR')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  )
}

function Stat({ label, value, color = 'text-cream' }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className={`font-mono text-3xl font-medium ${color}`}>{value}</div>
      <div className="text-muted text-sm mt-1">{label}</div>
    </div>
  )
}
