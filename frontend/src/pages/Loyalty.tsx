import { useEffect, useState } from 'react'
import { Star, TrendingUp, TrendingDown, Users } from 'lucide-react'
import { loyaltyApi, clientsApi } from '../api/client'
import type { LoyaltyOverview, LoyaltyTransactionResponse, LoyaltyTier } from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { TierBadge } from '../components/TierBadge'
import { PageSpinner } from '../components/Spinner'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

const tierColors: Record<LoyaltyTier, string> = {
  bronze:   'bg-amber-600',
  silver:   'bg-slate-400',
  gold:     'bg-gold',
  platinum: 'bg-violet-400',
}

export function Loyalty() {
  const [overview, setOverview] = useState<LoyaltyOverview | null>(null)
  const [txs, setTxs] = useState<LoyaltyTransactionResponse[]>([])
  const [clientMap, setClientMap] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      loyaltyApi.overview(),
      loyaltyApi.transactions({ limit: 50 }),
      clientsApi.list({ limit: 200 }),
    ])
      .then(([o, t, c]) => {
        setOverview(o)
        setTxs(t)
        const map: Record<number, string> = {}
        c.forEach(cl => { map[cl.id] = cl.name })
        setClientMap(map)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Layout><PageSpinner /></Layout>

  const totalTierClients = overview?.tier_distribution.reduce((s, t) => s + t.count, 0) ?? 0

  return (
    <Layout>
      <PageHeader title="Fidelidade" subtitle="Visão geral do programa de pontos" />

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="bg-gold/5 border-gold/20">
          <div className="flex items-center gap-2 text-gold text-xs font-semibold uppercase tracking-widest mb-3">
            <Star size={12} /> Total em circulação
          </div>
          <div className="font-mono text-3xl text-cream">{(overview?.total_points_in_circulation ?? 0).toLocaleString('pt-BR')}</div>
          <div className="text-muted text-xs mt-1">pontos</div>
        </Card>
        <Card className="bg-success/5 border-success/20">
          <div className="flex items-center gap-2 text-green-400 text-xs font-semibold uppercase tracking-widest mb-3">
            <TrendingUp size={12} /> Emitidos este mês
          </div>
          <div className="font-mono text-3xl text-cream">{(overview?.points_issued_this_month ?? 0).toLocaleString('pt-BR')}</div>
          <div className="text-muted text-xs mt-1">pontos</div>
        </Card>
        <Card className="bg-danger/5 border-danger/20">
          <div className="flex items-center gap-2 text-red-400 text-xs font-semibold uppercase tracking-widest mb-3">
            <TrendingDown size={12} /> Resgatados este mês
          </div>
          <div className="font-mono text-3xl text-cream">{(overview?.points_redeemed_this_month ?? 0).toLocaleString('pt-BR')}</div>
          <div className="text-muted text-xs mt-1">pontos</div>
        </Card>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Tier Distribution */}
        <Card>
          <div className="flex items-center gap-2 text-muted text-xs font-semibold uppercase tracking-widest mb-4">
            <Users size={12} /> Distribuição de Tiers
          </div>
          <div className="space-y-3">
            {overview?.tier_distribution.map(({ tier, count }) => (
              <div key={tier}>
                <div className="flex items-center justify-between mb-1">
                  <TierBadge tier={tier as LoyaltyTier} size="xs" />
                  <span className="font-mono text-sm text-cream">{count}</span>
                </div>
                <div className="h-1.5 bg-border rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${tierColors[tier as LoyaltyTier]}`}
                    style={{ width: `${totalTierClients > 0 ? (count / totalTierClients) * 100 : 0}%` }}
                  />
                </div>
                <div className="text-muted text-xs mt-0.5 text-right">
                  {totalTierClients > 0 ? ((count / totalTierClients) * 100).toFixed(0) : 0}%
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Clients */}
        <div className="col-span-2">
          <Card>
            <div className="text-muted text-xs font-semibold uppercase tracking-widest mb-4">Top Clientes por Pontos</div>
            <div className="divide-y divide-border">
              {overview?.top_clients.map((c, i) => (
                <div key={c.id} className="py-3 flex items-center gap-4">
                  <div className="w-6 text-center font-mono text-muted text-xs">#{i + 1}</div>
                  <div className="flex-1">
                    <div className="text-cream text-sm font-medium">{c.name}</div>
                    <div className="text-muted text-xs font-mono">{c.code}</div>
                  </div>
                  <TierBadge tier={c.tier as LoyaltyTier} size="xs" />
                  <div className="font-mono text-sm text-gold">{c.points.toLocaleString('pt-BR')} pts</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Transactions */}
      <Card>
        <div className="text-muted text-xs font-semibold uppercase tracking-widest mb-4">
          Últimas Transações ({txs.length})
        </div>
        {!txs.length ? (
          <div className="text-center py-8 text-muted text-sm">Nenhuma transação.</div>
        ) : (
          <div className="divide-y divide-border">
            {txs.map(tx => (
              <div key={tx.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="text-cream text-sm">{tx.description}</div>
                  <div className="text-muted text-xs font-mono">
                    {clientMap[tx.client_id] ?? `Cliente #${tx.client_id}`} &middot; {format(new Date(tx.created_at), "dd MMM yyyy HH:mm", { locale: ptBR })}
                  </div>
                </div>
                <div className={`font-mono text-sm font-semibold ${tx.type === 'redeemed' ? 'text-red-400' : 'text-green-400'}`}>
                  {tx.type === 'redeemed' ? '-' : '+'}{Math.abs(tx.points).toLocaleString('pt-BR')} pts
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </Layout>
  )
}
