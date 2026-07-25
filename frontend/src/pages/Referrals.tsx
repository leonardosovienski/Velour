import { useEffect, useState } from 'react'
import { Share2, Trophy } from 'lucide-react'
import { referralsApi, clientsApi } from '../api/client'
import type { ReferralResponse, ReferralRankingItem, ClientResponse } from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { PageSpinner } from '../components/Spinner'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

export function Referrals() {
  const [referrals, setReferrals] = useState<ReferralResponse[]>([])
  const [ranking, setRanking] = useState<ReferralRankingItem[]>([])
  const [clients, setClients] = useState<Record<number, ClientResponse>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      referralsApi.list({ limit: 100 }),
      referralsApi.ranking(),
      clientsApi.list({ limit: 200 }),
    ]).then(([r, rk, cl]) => {
      setReferrals(r)
      setRanking(rk)
      const map: Record<number, ClientResponse> = {}
      cl.forEach(c => { map[c.id] = c })
      setClients(map)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <Layout><PageSpinner /></Layout>

  const converted = referrals.filter(r => r.status === 'converted').length
  const pending = referrals.filter(r => r.status === 'pending').length

  return (
    <Layout>
      <PageHeader title="Indicações" subtitle="Rastreamento do programa de indicações" />

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card><Stat label="Total de Indicações" value={String(referrals.length)} /></Card>
        <Card className="bg-success/5 border-success/20"><Stat label="Convertidas" value={String(converted)} color="text-green-400" /></Card>
        <Card className="bg-yellow-900/10 border-yellow-800/20"><Stat label="Pendentes" value={String(pending)} color="text-yellow-400" /></Card>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Ranking */}
        <Card>
          <div className="flex items-center gap-2 text-gold text-xs font-semibold uppercase tracking-widest mb-4">
            <Trophy size={12} /> Top Indicadores
          </div>
          {!ranking.length ? (
            <div className="text-muted text-sm text-center py-6">Sem dados ainda.</div>
          ) : (
            <div className="space-y-3">
              {ranking.map((r, i) => (
                <div key={r.client_id} className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${i === 0 ? 'bg-gold text-bg' : i === 1 ? 'bg-slate-400 text-bg' : i === 2 ? 'bg-amber-700 text-cream' : 'bg-border text-muted'}`}>
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-cream text-sm truncate">{r.name}</div>
                    <div className="text-muted text-xs font-mono">{r.code}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-sm text-cream">{r.conversions}</div>
                    <div className="text-muted text-xs">conv.</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Referral List */}
        <div className="col-span-2">
          <Card>
            <div className="flex items-center gap-2 text-muted text-xs font-semibold uppercase tracking-widest mb-4">
              <Share2 size={12} /> Histórico ({referrals.length})
            </div>
            {!referrals.length ? (
              <div className="text-center py-8 text-muted text-sm">Nenhuma indicação registrada.</div>
            ) : (
              <div className="divide-y divide-border">
                {referrals.map(ref => {
                  const referrer = clients[ref.referrer_id]
                  const referred = clients[ref.referred_id]
                  return (
                    <div key={ref.id} className="py-3 flex items-center justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="text-cream text-sm flex items-center gap-2 flex-wrap">
                          <span className="font-medium">{referrer?.name ?? `#${ref.referrer_id}`}</span>
                          <span className="text-muted">→</span>
                          <span>{referred?.name ?? `#${ref.referred_id}`}</span>
                        </div>
                        <div className="text-muted text-xs mt-0.5">
                          {format(new Date(ref.created_at), "dd MMM yyyy", { locale: ptBR })}
                          {ref.converted_at && ` · convertido em ${format(new Date(ref.converted_at), "dd MMM yyyy", { locale: ptBR })}`}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        {ref.status === 'converted' && (
                          <div className="text-xs text-muted text-right">
                            <div className="text-green-400">+{ref.points_awarded_referrer} pts</div>
                            <div className="text-green-400/70">+{ref.points_awarded_referred} pts</div>
                          </div>
                        )}
                        <span className={`text-xs px-2.5 py-1 rounded-full border ${ref.status === 'converted' ? 'text-green-400 border-success/40 bg-success/10' : 'text-yellow-400 border-yellow-800/40 bg-yellow-900/20'}`}>
                          {ref.status === 'converted' ? 'Convertida' : 'Pendente'}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>
      </div>
    </Layout>
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
