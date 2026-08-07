import { useEffect, useState, type FormEvent } from 'react'
import { TrendingUp, Scissors, Plus, Pencil, ToggleLeft, ToggleRight, Gauge, Target, UserX } from 'lucide-react'
import { professionalsApi, getErrorDetail } from '../api/client'
import type { ProfessionalResponse, ProfessionalStats, ProfessionalCreate, ProfessionalDashboard, Gender } from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { Modal } from '../components/Modal'
import { TierBadge } from '../components/TierBadge'
import { PageSpinner, Spinner } from '../components/Spinner'

export function Professionals() {
  const [professionals, setProfessionals] = useState<ProfessionalResponse[]>([])
  const [stats, setStats] = useState<Record<number, ProfessionalStats>>({})
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<ProfessionalResponse | null>(null)
  const [panelFor, setPanelFor] = useState<ProfessionalResponse | null>(null)

  async function load() {
    setLoading(true)
    const profs = await professionalsApi.list()
    setProfessionals(profs)
    const statsArr = await Promise.all(profs.map(p => professionalsApi.stats(p.id)))
    const statsMap: Record<number, ProfessionalStats> = {}
    statsArr.forEach(s => { statsMap[s.professional_id] = s })
    setStats(statsMap)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function handleToggleActive(prof: ProfessionalResponse) {
    await professionalsApi.update(prof.id, { is_active: !prof.is_active })
    load()
  }

  return (
    <Layout>
      <PageHeader
        title="Profissionais"
        subtitle={`${professionals.length} profissionais ativos`}
        action={
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors"
          >
            <Plus size={16} /> Novo Profissional
          </button>
        }
      />

      {loading ? <PageSpinner /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {professionals.map(prof => {
            const s = stats[prof.id]
            return (
              <Card key={prof.id} className={`hover:border-border/80 ${!prof.is_active ? 'opacity-50' : ''}`}>
                <div className="flex items-start gap-3 mb-4">
                  <div className="w-11 h-11 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
                    <span className="font-display text-lg text-gold font-semibold">
                      {prof.name.charAt(0)}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-cream font-medium truncate">{prof.name}</div>
                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <button
                          onClick={() => setPanelFor(prof)}
                          title="Painel do profissional"
                          className="text-muted hover:text-gold p-1 transition-colors"
                        >
                          <Gauge size={14} />
                        </button>
                        <button
                          onClick={() => setEditing(prof)}
                          title="Editar"
                          className="text-muted hover:text-gold p-1 transition-colors"
                        >
                          <Pencil size={13} />
                        </button>
                        <button
                          onClick={() => handleToggleActive(prof)}
                          title={prof.is_active ? 'Desativar' : 'Ativar'}
                          className={`p-1 transition-colors ${prof.is_active ? 'text-success hover:text-red-400' : 'text-muted hover:text-success'}`}
                        >
                          {prof.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 text-muted text-xs mt-0.5">
                      <Scissors size={11} /> {prof.specialty}
                    </div>
                    {prof.bio && <div className="text-muted text-xs mt-1 line-clamp-2">{prof.bio}</div>}
                  </div>
                </div>

                <div className="text-xs text-muted mb-4">
                  Comissão: <span className="text-cream font-mono">{(prof.commission_rate * 100).toFixed(0)}%</span>
                  {prof.email && <span className="ml-3 text-muted">{prof.email}</span>}
                </div>

                {s && (
                  <div className="border-t border-border pt-4">
                    <div className="flex items-center gap-1.5 text-gold text-xs font-semibold uppercase tracking-widest mb-3">
                      <TrendingUp size={11} /> Este mês
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <Stat label="Atend." value={String(s.appointments_this_month)} />
                      <Stat label="Receita" value={`R$${Math.round(s.revenue_this_month)}`} />
                      <Stat label="Comissão" value={`R$${Math.round(s.commission_this_month)}`} />
                    </div>
                    {s.top_service && (
                      <div className="mt-3 text-xs text-muted">
                        Top serviço: <span className="text-cream">{s.top_service}</span>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            )
          })}

          {!professionals.length && (
            <div className="col-span-3 text-center py-16 text-muted">Nenhum profissional cadastrado.</div>
          )}
        </div>
      )}

      <ProfessionalModal
        open={creating || !!editing}
        professional={editing}
        onClose={() => { setCreating(false); setEditing(null) }}
        onSuccess={() => { setCreating(false); setEditing(null); load() }}
      />

      <DashboardModal professional={panelFor} onClose={() => setPanelFor(null)} />
    </Layout>
  )
}

function DashboardModal({ professional, onClose }: { professional: ProfessionalResponse | null; onClose: () => void }) {
  const [data, setData] = useState<ProfessionalDashboard | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!professional) { setData(null); return }
    setLoading(true)
    professionalsApi.dashboard(professional.id).then(setData).finally(() => setLoading(false))
  }, [professional])

  const goal = data?.monthly_goal
  const pct = goal?.progress != null ? Math.min(goal.progress * 100, 100) : null

  return (
    <Modal title={`Painel — ${professional?.name ?? ''}`} open={!!professional} onClose={onClose} width="max-w-lg">
      {loading || !data ? (
        <div className="py-10 flex justify-center"><Spinner size={28} /></div>
      ) : (
        <div className="space-y-5">
          {/* Meta do mês */}
          <div>
            <div className="flex items-center gap-1.5 text-gold text-xs font-semibold uppercase tracking-widest mb-3">
              <Target size={12} /> Meta do mês
            </div>
            {goal && goal.target > 0 ? (
              <>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="text-cream font-mono">R${goal.revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                  <span className="text-muted font-mono">de R${goal.target.toLocaleString('pt-BR')}</span>
                </div>
                <div className="h-2.5 bg-bg border border-border rounded-full overflow-hidden">
                  <div className="h-full bg-gold rounded-full transition-all" style={{ width: `${pct}%` }} />
                </div>
                <div className="flex justify-between text-xs text-muted mt-1.5">
                  <span>{pct?.toFixed(0)}% atingido</span>
                  {goal.remaining != null && <span>Faltam R${goal.remaining.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>}
                </div>
                <div className="text-xs text-muted mt-2">Comissão acumulada: <span className="text-cream font-mono">R${goal.commission.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span></div>
              </>
            ) : (
              <div className="text-muted text-sm">Nenhuma meta definida. Edite o profissional para configurar.</div>
            )}
          </div>

          {/* Clientes inativos */}
          <div className="border-t border-border pt-4">
            <div className="flex items-center gap-1.5 text-gold text-xs font-semibold uppercase tracking-widest mb-3">
              <UserX size={12} /> Clientes a recuperar ({data.inactive_clients.length})
            </div>
            {!data.inactive_clients.length ? (
              <div className="text-muted text-sm">Nenhum cliente fora da cadência habitual. 🎉</div>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {data.inactive_clients.map(c => (
                  <div key={c.client_id} className="flex items-center justify-between gap-3 bg-bg border border-border rounded-lg px-3 py-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-cream text-sm truncate">{c.name}</span>
                        <TierBadge tier={c.tier} size="xs" />
                      </div>
                      <div className="text-muted text-xs">
                        Cadência ~{c.avg_cadence_days}d · sem vir há {c.days_since_last}d
                      </div>
                    </div>
                    <span className="text-danger font-mono text-xs flex-shrink-0">+{c.overdue_by_days}d</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}

function ProfessionalModal({ open, professional, onClose, onSuccess }: {
  open: boolean
  professional: ProfessionalResponse | null
  onClose: () => void
  onSuccess: () => void
}) {
  const blank: ProfessionalCreate = { name: '', phone: '', gender: 'F', specialty: '', commission_rate: 0.40, monthly_goal: 0 }
  const [form, setForm] = useState<ProfessionalCreate>(blank)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (professional) {
      setForm({
        name: professional.name,
        phone: professional.phone,
        email: professional.email,
        gender: professional.gender,
        specialty: professional.specialty,
        bio: professional.bio,
        commission_rate: professional.commission_rate,
        monthly_goal: professional.monthly_goal,
      })
    } else {
      setForm(blank)
    }
    setError('')
  }, [professional, open])

  function set(field: keyof ProfessionalCreate, value: string | number) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (professional) {
        await professionalsApi.update(professional.id, form)
      } else {
        await professionalsApi.create(form)
      }
      onSuccess()
    } catch (err) {
      setError(getErrorDetail(err) ?? 'Erro ao salvar profissional.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={professional ? 'Editar Profissional' : 'Novo Profissional'} open={open} onClose={onClose} width="max-w-xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="field-label">Nome completo *</label>
            <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="Ana Luiza Ferreira" required />
          </div>
          <div>
            <label className="field-label">Telefone *</label>
            <input value={form.phone} onChange={e => set('phone', e.target.value)} placeholder="(11) 99999-9999" required />
          </div>
          <div>
            <label className="field-label">Email</label>
            <input type="email" value={form.email ?? ''} onChange={e => set('email', e.target.value)} placeholder="opcional" />
          </div>
          <div>
            <label className="field-label">Gênero *</label>
            <select value={form.gender} onChange={e => set('gender', e.target.value as Gender)}>
              <option value="F">Feminino</option>
              <option value="M">Masculino</option>
              <option value="other">Outro</option>
            </select>
          </div>
          <div>
            <label className="field-label">Comissão (%) *</label>
            <input
              type="number" min="0" max="100" step="1"
              value={Math.round(form.commission_rate * 100)}
              onChange={e => set('commission_rate', Number(e.target.value) / 100)}
              required
            />
          </div>
          <div className="col-span-2">
            <label className="field-label">Meta financeira do mês (R$)</label>
            <input
              type="number" min="0" step="100"
              value={form.monthly_goal ?? 0}
              onChange={e => set('monthly_goal', Number(e.target.value) || 0)}
            />
          </div>
          <div className="col-span-2">
            <label className="field-label">Especialidade *</label>
            <input value={form.specialty} onChange={e => set('specialty', e.target.value)} placeholder="ex: Coloração, Corte Feminino, Mechas" required />
          </div>
          <div className="col-span-2">
            <label className="field-label">Bio</label>
            <textarea value={form.bio ?? ''} onChange={e => set('bio', e.target.value)} rows={2} placeholder="Breve descrição do profissional…" />
          </div>
        </div>

        {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
            {loading ? <Spinner size={16} /> : (professional ? 'Salvar' : 'Criar Profissional')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-base text-cream font-medium">{value}</div>
      <div className="text-muted text-xs">{label}</div>
    </div>
  )
}
