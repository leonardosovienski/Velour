import { useEffect, useState, type FormEvent } from 'react'
import { format } from 'date-fns'
import { Plus, Search, CheckCircle, XCircle, BookOpen, ChevronDown } from 'lucide-react'
import { appointmentsApi, clientsApi, professionalsApi, servicesApi, recipesApi } from '../api/client'
import type {
  AppointmentDetail, ClientResponse, ProfessionalResponse,
  ServiceResponse, AppointmentCreate, AppointmentComplete,
  ServiceRecipeResponse, RecipeOverride, LoyaltyTier,
} from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { StatusBadge } from '../components/StatusBadge'
import { TierBadge } from '../components/TierBadge'
import { BriefingDrawer } from '../components/BriefingDrawer'
import { Modal } from '../components/Modal'
import { PageSpinner, Spinner } from '../components/Spinner'

const statusOptions = [
  { value: '', label: 'Todos os status' },
  { value: 'scheduled', label: 'Agendado' },
  { value: 'confirmed', label: 'Confirmado' },
  { value: 'in_progress', label: 'Em atendimento' },
  { value: 'completed', label: 'Concluído' },
  { value: 'cancelled', label: 'Cancelado' },
  { value: 'no_show', label: 'Não compareceu' },
]

export function Appointments() {
  const [appointments, setAppointments] = useState<AppointmentDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [search, setSearch] = useState('')
  const [creating, setCreating] = useState(false)
  const [completing, setCompleting] = useState<AppointmentDetail | null>(null)
  const [briefingClientId, setBriefingClientId] = useState<number | null>(null)
  const [cancelId, setCancelId] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    const data = await appointmentsApi.list({
      status: statusFilter || undefined,
      date_from: dateFrom || undefined,
      limit: 100,
    })
    setAppointments(data)
    setLoading(false)
  }

  useEffect(() => { load() }, [statusFilter, dateFrom])

  const filtered = appointments.filter(a => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      a.client?.name.toLowerCase().includes(q) ||
      a.professional?.name.toLowerCase().includes(q) ||
      a.service?.name.toLowerCase().includes(q)
    )
  })

  async function handleCancel(id: number) {
    await appointmentsApi.cancel(id)
    setCancelId(null)
    load()
  }

  async function handleStatusChange(id: number, status: string) {
    await appointmentsApi.updateStatus(id, status)
    load()
  }

  return (
    <Layout>
      <PageHeader
        title="Agendamentos"
        subtitle={`${appointments.length} agendamentos`}
        action={
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors"
          >
            <Plus size={16} /> Novo Agendamento
          </button>
        }
      />

      {/* Filters */}
      <div className="flex gap-3 mb-6 flex-wrap">
        <div className="relative flex-1 min-w-48 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar cliente, profissional…" className="pl-9" />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="w-44">
          {statusOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="w-40" />
        {dateFrom && (
          <button onClick={() => setDateFrom('')} className="text-muted hover:text-cream text-sm px-2">✕ Limpar data</button>
        )}
      </div>

      {loading ? <PageSpinner /> : (
        <div className="space-y-2">
          {!filtered.length ? (
            <div className="text-center py-16 text-muted">Nenhum agendamento encontrado.</div>
          ) : filtered.map(appt => (
            <AppointmentRow
              key={appt.id}
              appt={appt}
              onComplete={() => setCompleting(appt)}
              onCancel={() => setCancelId(appt.id)}
              onBriefing={() => setBriefingClientId(appt.client_id)}
              onStatusChange={(s) => handleStatusChange(appt.id, s)}
            />
          ))}
        </div>
      )}

      <CreateModal open={creating} onClose={() => setCreating(false)} onSuccess={() => { setCreating(false); load() }} />
      <CompleteModal appt={completing} onClose={() => setCompleting(null)} onSuccess={() => { setCompleting(null); load() }} />
      <BriefingDrawer clientId={briefingClientId} onClose={() => setBriefingClientId(null)} />
      <Modal title="Cancelar agendamento" open={cancelId !== null} onClose={() => setCancelId(null)} width="max-w-sm">
        <p className="text-muted text-sm mb-5">Esta ação não pode ser desfeita. Confirma o cancelamento?</p>
        <div className="flex justify-end gap-3">
          <button onClick={() => setCancelId(null)} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">
            Voltar
          </button>
          <button
            onClick={() => cancelId !== null && handleCancel(cancelId)}
            className="flex items-center gap-2 bg-danger hover:bg-danger/90 text-cream font-semibold px-5 py-2 rounded-lg text-sm"
          >
            Cancelar agendamento
          </button>
        </div>
      </Modal>
    </Layout>
  )
}

function AppointmentRow({ appt, onComplete, onCancel, onBriefing, onStatusChange }: {
  appt: AppointmentDetail
  onComplete: () => void
  onCancel: () => void
  onBriefing: () => void
  onStatusChange: (s: string) => void
}) {
  const [showStatus, setShowStatus] = useState(false)
  const canComplete = ['confirmed', 'in_progress', 'scheduled'].includes(appt.status)
  const canCancel = !['completed', 'cancelled'].includes(appt.status)

  return (
    <Card className="hover:border-border/80">
      <div className="flex items-center gap-4">
        {/* Time */}
        <div className="w-20 flex-shrink-0 text-right">
          <div className="font-mono text-gold font-medium">{format(new Date(appt.scheduled_at), 'HH:mm')}</div>
          <div className="font-mono text-muted text-xs">{format(new Date(appt.scheduled_at), 'dd/MM')}</div>
        </div>

        {/* Client */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-cream font-medium">{appt.client?.name ?? `Cliente #${appt.client_id}`}</span>
            {appt.client && <TierBadge tier={appt.client.loyalty_tier} size="xs" />}
          </div>
          <div className="text-muted text-xs">{appt.service?.name} &middot; {appt.professional?.name}</div>
        </div>

        {/* Duration / Price */}
        <div className="text-right hidden md:block">
          <div className="text-muted text-xs">{appt.service?.duration_minutes} min</div>
          {appt.price_charged != null && (
            <div className="font-mono text-sm text-cream">R${appt.price_charged.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</div>
          )}
        </div>

        {/* Status */}
        <div className="flex-shrink-0">
          <StatusBadge status={appt.status} />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button onClick={onBriefing} title="Briefing" className="text-muted hover:text-gold p-1.5 rounded hover:bg-gold/10 transition-colors">
            <BookOpen size={14} />
          </button>

          <div className="relative">
            <button onClick={() => setShowStatus(s => !s)} title="Mudar status" className="text-muted hover:text-cream p-1.5 rounded hover:bg-white/5 transition-colors">
              <ChevronDown size={14} />
            </button>
            {showStatus && (
              <div className="absolute right-0 top-8 z-20 bg-surface border border-border rounded-lg shadow-xl py-1 w-44">
                {statusOptions.filter(o => o.value).map(o => (
                  <button
                    key={o.value}
                    onClick={() => { onStatusChange(o.value); setShowStatus(false) }}
                    className="block w-full text-left px-4 py-2 text-sm text-muted hover:text-cream hover:bg-white/5"
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {canComplete && (
            <button onClick={onComplete} title="Concluir" className="text-green-500 hover:text-green-400 p-1.5 rounded hover:bg-success/10 transition-colors">
              <CheckCircle size={14} />
            </button>
          )}
          {canCancel && (
            <button onClick={onCancel} title="Cancelar" className="text-danger/70 hover:text-red-400 p-1.5 rounded hover:bg-danger/10 transition-colors">
              <XCircle size={14} />
            </button>
          )}
        </div>
      </div>
    </Card>
  )
}

function CreateModal({ open, onClose, onSuccess }: { open: boolean; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState<AppointmentCreate>({
    client_id: 0, professional_id: 0, service_id: 0, scheduled_at: '',
  })
  const [clients, setClients] = useState<ClientResponse[]>([])
  const [professionals, setProfessionals] = useState<ProfessionalResponse[]>([])
  const [services, setServices] = useState<ServiceResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    Promise.all([
      clientsApi.list({ limit: 200 }),
      professionalsApi.list(),
      servicesApi.list(),
    ]).then(([c, p, s]) => { setClients(c); setProfessionals(p); setServices(s) })
  }, [open])

  function set(field: keyof AppointmentCreate, value: string | number) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await appointmentsApi.create({
        ...form,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
      })
      onSuccess()
      setForm({ client_id: 0, professional_id: 0, service_id: 0, scheduled_at: '' })
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'Erro ao criar agendamento. Verifique conflito de horário.')
    } finally {
      setLoading(false)
    }
  }

  const selectedService = services.find(s => s.id === form.service_id)

  return (
    <Modal title="Novo Agendamento" open={open} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="field-label">Cliente *</label>
          <select value={form.client_id} onChange={e => set('client_id', Number(e.target.value))} required>
            <option value={0}>Selecione um cliente</option>
            {clients.map(c => <option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}
          </select>
        </div>
        <div>
          <label className="field-label">Profissional *</label>
          <select value={form.professional_id} onChange={e => set('professional_id', Number(e.target.value))} required>
            <option value={0}>Selecione um profissional</option>
            {professionals.map(p => <option key={p.id} value={p.id}>{p.name} — {p.specialty}</option>)}
          </select>
        </div>
        <div>
          <label className="field-label">Serviço *</label>
          <select value={form.service_id} onChange={e => set('service_id', Number(e.target.value))} required>
            <option value={0}>Selecione um serviço</option>
            {services.map(s => <option key={s.id} value={s.id}>{s.name} — {s.duration_minutes}min — R${s.price.toFixed(2)}</option>)}
          </select>
        </div>
        {selectedService && (
          <div className="bg-bg rounded-lg p-3 text-xs text-muted border border-border">
            Duração: {selectedService.duration_minutes} min &middot; Preço: R${selectedService.price.toFixed(2)} &middot; {selectedService.points_reward} pts
          </div>
        )}
        <div>
          <label className="field-label">Data e Horário *</label>
          <input type="datetime-local" value={form.scheduled_at} onChange={e => set('scheduled_at', e.target.value)} required />
        </div>
        <div>
          <label className="field-label">Ocasião</label>
          <input value={form.occasion ?? ''} onChange={e => set('occasion', e.target.value)} placeholder="ex: Casamento, Formatura" />
        </div>
        <div>
          <label className="field-label">Observações</label>
          <textarea value={form.notes ?? ''} onChange={e => set('notes', e.target.value)} rows={2} placeholder="Observações sobre o agendamento…" />
        </div>

        {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
            {loading ? <Spinner size={16} /> : 'Agendar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

const TIER_RATES: Record<LoyaltyTier, number> = { bronze: 0, silver: 0.05, gold: 0.10, platinum: 0.15 }
const TIER_LABEL: Record<LoyaltyTier, string> = { bronze: 'Bronze', silver: 'Silver', gold: 'Gold', platinum: 'Platinum' }

function CompleteModal({ appt, onClose, onSuccess }: { appt: AppointmentDetail | null; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState<AppointmentComplete>({ price_charged: 0, discount_points_used: 0 })
  const [photoBefore, setPhotoBefore] = useState<File | null>(null)
  const [photoAfter, setPhotoAfter] = useState<File | null>(null)
  const [recipe, setRecipe] = useState<ServiceRecipeResponse[]>([])
  const [overrides, setOverrides] = useState<Record<number, number>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!appt) return
    setForm({ price_charged: appt.service?.price ?? 0, discount_points_used: 0 })
    setPhotoBefore(null); setPhotoAfter(null); setRecipe([]); setOverrides({})
    if (appt.service_id) {
      recipesApi.get(appt.service_id).then(r => {
        setRecipe(r)
        setOverrides(Object.fromEntries(r.map(i => [i.product_id, i.qty_consumed])))
      }).catch(() => setRecipe([]))
    }
  }, [appt])

  function set(field: keyof AppointmentComplete, value: string | number) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!appt) return
    setError('')
    setLoading(true)
    try {
      // Só envia overrides dos insumos que o profissional alterou
      const recipe_overrides: RecipeOverride[] = recipe
        .filter(i => overrides[i.product_id] !== i.qty_consumed)
        .map(i => ({ product_id: i.product_id, actual_qty: overrides[i.product_id] ?? i.qty_consumed }))
      await appointmentsApi.complete(appt.id, {
        ...form,
        recipe_overrides: recipe_overrides.length ? recipe_overrides : undefined,
      })
      if (photoBefore || photoAfter) {
        await appointmentsApi.uploadPhotos(appt.id, photoBefore ?? undefined, photoAfter ?? undefined)
      }
      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Erro ao concluir atendimento.')
    } finally {
      setLoading(false)
    }
  }

  const base = form.price_charged ?? 0
  const tier: LoyaltyTier = appt?.client?.loyalty_tier ?? 'bronze'
  const tierRate = TIER_RATES[tier]
  const tierDiscount = base * tierRate
  const maxTotal = base * 0.5
  const pointsRaw = ((form.discount_points_used ?? 0) / 100) * 10
  const pointsDiscount = Math.min(pointsRaw, Math.max(maxTotal - tierDiscount, 0))
  const finalPrice = Math.max(0, base - tierDiscount - pointsDiscount)

  return (
    <Modal title="Concluir Atendimento" open={!!appt} onClose={onClose}>
      {appt && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-bg rounded-lg p-3 border border-border text-sm">
            <div className="text-cream font-medium">{appt.client?.name}</div>
            <div className="text-muted text-xs">{appt.service?.name} &middot; {appt.professional?.name}</div>
          </div>

          <div>
            <label className="field-label">Valor cobrado (R$) *</label>
            <input type="number" step="0.01" min="0" value={form.price_charged}
              onChange={e => set('price_charged', parseFloat(e.target.value) || 0)} required />
          </div>

          <div>
            <label className="field-label">Pontos a resgatar (múltiplos de 100)</label>
            <input type="number" step="100" min="0" value={form.discount_points_used ?? 0}
              onChange={e => set('discount_points_used', parseInt(e.target.value) || 0)} />
          </div>

          {/* Resumo de descontos */}
          <div className="bg-bg rounded-lg p-3 border border-border space-y-1.5 text-sm">
            <div className="flex justify-between text-muted"><span>Valor base</span><span className="font-mono text-cream">R${base.toFixed(2)}</span></div>
            <div className="flex justify-between text-muted">
              <span>Desconto {TIER_LABEL[tier]} ({(tierRate * 100).toFixed(0)}%)</span>
              <span className="font-mono text-gold">−R${tierDiscount.toFixed(2)}</span>
            </div>
            {pointsDiscount > 0 && (
              <div className="flex justify-between text-muted">
                <span>Resgate de pontos</span>
                <span className="font-mono text-gold">−R${pointsDiscount.toFixed(2)}</span>
              </div>
            )}
            {pointsRaw > pointsDiscount && (
              <div className="text-amber-400 text-xs">Desconto combinado limitado a 50% do valor base.</div>
            )}
            <div className="flex justify-between border-t border-border pt-1.5 font-medium">
              <span className="text-cream">Valor final</span><span className="font-mono text-cream">R${finalPrice.toFixed(2)}</span>
            </div>
          </div>

          {/* Ajuste de insumos (ficha técnica) */}
          {recipe.length > 0 && (
            <div className="bg-bg rounded-lg p-3 border border-border">
              <div className="text-muted text-xs uppercase tracking-widest mb-2">Insumos consumidos (ficha técnica)</div>
              <div className="space-y-2">
                {recipe.map(i => (
                  <div key={i.product_id} className="flex items-center justify-between gap-3">
                    <span className="text-sm text-cream truncate">{i.product_name}</span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <input type="number" step="0.01" min="0" value={overrides[i.product_id] ?? i.qty_consumed}
                        onChange={e => setOverrides(o => ({ ...o, [i.product_id]: parseFloat(e.target.value) || 0 }))}
                        className="w-24 text-right" />
                      <span className="text-muted text-xs w-6">{i.unit}</span>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-muted text-xs mt-2">Ajuste a dosagem real usada; a baixa de estoque segue esses valores.</p>
            </div>
          )}

          <div>
            <label className="field-label">Fórmula utilizada (coloração)</label>
            <input value={form.formula_used ?? ''} onChange={e => set('formula_used', e.target.value)} placeholder="ex: Wella 6/7 + ox 20vol" />
          </div>

          <div>
            <label className="field-label">Observações do atendimento</label>
            <textarea value={form.notes ?? ''} onChange={e => set('notes', e.target.value)} rows={2} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="field-label">Foto antes</label>
              <input type="file" accept="image/*" onChange={e => setPhotoBefore(e.target.files?.[0] ?? null)}
                className="text-xs text-muted file:mr-2 file:text-xs file:px-3 file:py-1.5 file:rounded file:border-0 file:bg-gold/10 file:text-gold hover:file:bg-gold/20" />
              {photoBefore && <p className="text-muted text-xs mt-1 truncate">{photoBefore.name}</p>}
            </div>
            <div>
              <label className="field-label">Foto depois</label>
              <input type="file" accept="image/*" onChange={e => setPhotoAfter(e.target.files?.[0] ?? null)}
                className="text-xs text-muted file:mr-2 file:text-xs file:px-3 file:py-1.5 file:rounded file:border-0 file:bg-gold/10 file:text-gold hover:file:bg-gold/20" />
              {photoAfter && <p className="text-muted text-xs mt-1 truncate">{photoAfter.name}</p>}
            </div>
          </div>

          {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
            <button type="submit" disabled={loading} className="flex items-center gap-2 bg-success hover:bg-success/90 text-cream font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
              {loading ? <Spinner size={16} /> : 'Concluir Atendimento'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  )
}
