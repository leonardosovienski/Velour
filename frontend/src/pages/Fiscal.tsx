import { Fragment, useEffect, useState, type FormEvent } from 'react'
import { Download, FileText, Plus, RefreshCw } from 'lucide-react'
import { fiscalApi, getErrorDetail } from '../api/client'
import type { FiscalAppointment, FiscalConfig, FiscalDocument, FiscalEvent, FiscalParty, FiscalProfile, FiscalTenant } from '../api/fiscalTypes'
import { Layout, Card, PageHeader } from '../components/Layout'
import { useAuth } from '../context/useAuth'

const emptyParty: FiscalParty = { legal_name: '', tax_id: '', email: null, street: '', number: '', district: '', postal_code: '', city: 'Araucária', municipality_code: '4101804', state: 'PR' }
const emptyProfile: FiscalProfile = { ...emptyParty, municipal_registration: '', tax_regime: 'mei', service_code: '', iss_rate: 0 }
const inputStyle = 'w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-cream text-sm focus:outline-none focus:border-gold'
const labels = { draft: 'Rascunho', simulated: 'Emitida em demonstração', cancelled: 'Cancelada' }
const actionLabels: Record<string, string> = { created: 'Rascunho criado', simulate: 'Emissão simulada', cancel: 'Documento cancelado' }
const money = (value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

function Field({ label, value, onChange, type = 'text', required = true, ...rest }: {
  label: string; value: string | number; onChange: (v: string) => void; type?: string; required?: boolean
  min?: string; max?: string; step?: string; maxLength?: number; pattern?: string
}) {
  return <label className="block text-sm text-muted"><span className="block mb-1.5">{label}</span><input {...rest} type={type} className={inputStyle} value={value} required={required} onChange={e => onChange(e.target.value)} /></label>
}

function PartyFields({ value, onChange }: { value: FiscalParty; onChange: (v: FiscalParty) => void }) {
  const set = (key: keyof FiscalParty, next: string) => onChange({ ...value, [key]: key === 'email' ? next || null : next })
  return <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
    <Field label="Nome / razão social" value={value.legal_name} onChange={v => set('legal_name', v)} maxLength={150} />
    <Field label="CPF / CNPJ" value={value.tax_id} onChange={v => set('tax_id', v)} maxLength={20} />
    <Field label="E-mail (opcional)" type="email" required={false} value={value.email || ''} onChange={v => set('email', v)} />
    <Field label="Logradouro" value={value.street} onChange={v => set('street', v)} maxLength={120} />
    <Field label="Número" value={value.number} onChange={v => set('number', v)} maxLength={20} />
    <Field label="Bairro" value={value.district} onChange={v => set('district', v)} maxLength={60} />
    <Field label="CEP (8 dígitos)" value={value.postal_code} onChange={v => set('postal_code', v)} pattern="[0-9]{8}" />
    <Field label="Município" value={value.city} onChange={v => set('city', v)} maxLength={60} />
    <Field label="Código IBGE" value={value.municipality_code} onChange={v => set('municipality_code', v)} pattern="[0-9]{7}" />
    <Field label="UF" value={value.state} onChange={v => set('state', v.toUpperCase())} maxLength={2} />
  </div>
}

export function Fiscal({ embedded = false, fixedScope, appointmentId, documentId }: { embedded?: boolean; fixedScope?: 'salon' | 'received' | 'platform'; appointmentId?: number; documentId?: number }) {
  const Wrapper = embedded ? Fragment : Layout
  const { user } = useAuth()
  const [config, setConfig] = useState<FiscalConfig | null>(null)
  const [scope, setScope] = useState<'salon' | 'received' | 'platform'>(fixedScope || 'salon')
  const platform = scope === 'platform'
  const [profile, setProfile] = useState<FiscalProfile>(emptyProfile)
  const [hasProfile, setHasProfile] = useState(false)
  const [documents, setDocuments] = useState<FiscalDocument[]>([])
  const [appointments, setAppointments] = useState<FiscalAppointment[]>([])
  const [tenants, setTenants] = useState<FiscalTenant[]>([])
  const [selected, setSelected] = useState<FiscalDocument | null>(null)
  const [events, setEvents] = useState<FiscalEvent[]>([])
  const [editingProfile, setEditingProfile] = useState(false)
  const [creating, setCreating] = useState(!!appointmentId)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [revision, setRevision] = useState(0)
  const [offset, setOffset] = useState(0)
  const [cancelReason, setCancelReason] = useState('')
  const [showCancel, setShowCancel] = useState(false)

  useEffect(() => {
    if (user?.role !== 'admin') return
    let active = true
    setLoading(true)
    setError('')
    Promise.all([fiscalApi.config(), fiscalApi.profile(platform), fiscalApi.list(platform, scope === 'received', offset),
      platform ? fiscalApi.tenants() : fiscalApi.appointments()]).then(([c, p, docs, sources]) => {
      if (!active) return
      setConfig(c); setProfile(p || emptyProfile); setHasProfile(!!p); setDocuments(docs)
      if (platform) setTenants(sources as FiscalTenant[])
      else setAppointments(sources as FiscalAppointment[])
      if (documentId && !platform && revision === 0) {
        fiscalApi.get(documentId).then(doc => { if (active) { setSelected(doc); return fiscalApi.events(doc.id, false) } }).then(history => { if (active && history) setEvents(history) }).catch(err => { if (active) setError(getErrorDetail(err) || 'Documento não encontrado.') })
      }
    }).catch(err => { if (active) setError(getErrorDetail(err) || 'Não foi possível carregar o módulo fiscal.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [scope, platform, revision, offset, user?.role, documentId])

  async function act(fn: () => Promise<void>) {
    setBusy(true); setError(''); setMessage('')
    try { await fn() } catch (err) { setError(getErrorDetail(err) || 'Não foi possível concluir a operação. Tente novamente.') }
    finally { setBusy(false) }
  }

  async function inspect(doc: FiscalDocument) {
    setSelected(doc); setEvents([]); setShowCancel(false); setCancelReason('')
    await act(async () => setEvents(await fiscalApi.events(doc.id, platform)))
  }

  function switchScope(next: typeof scope) {
    setScope(next); setOffset(0); setSelected(null); setCreating(false); setEditingProfile(false); setMessage('')
  }

  async function download(doc: FiscalDocument) {
    await act(async () => {
      const blob = await fiscalApi.print(doc.id, platform)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a'); link.href = url; link.download = `velour-demo-${doc.id}.html`
      document.body.appendChild(link); link.click(); link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      setMessage('Demonstrativo baixado. Abra o arquivo e use Imprimir para salvar em PDF.')
    })
  }

  if (user?.role !== 'admin') return <Wrapper><PageHeader title="Fiscal" /><p className="text-muted">O módulo fiscal é gerenciado pelo administrador do salão.</p></Wrapper>
  const enabled = config?.mode === 'demo'
  return <Wrapper>
    <PageHeader title={scope === 'received' ? 'Documentos da assinatura' : scope === 'platform' ? 'Documentos de assinantes' : 'Documentos fiscais'} subtitle="Cadastros, documentos de serviços e notas da assinatura." action={<button className="secondary-button" disabled={busy || loading} onClick={() => setRevision(v => v + 1)}><RefreshCw size={16} /> Atualizar</button>} />
    <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-200 p-4 mb-6" role="note">
      <strong className="block">Demonstração — sem validade fiscal</strong>
      <p className="text-sm mt-1">Nenhum documento é enviado à Receita ou à prefeitura. Valores de ISS são ilustrativos.</p>
    </div>
    {!fixedScope && <div role="tablist" aria-label="Origem dos documentos" className="flex flex-wrap gap-2 mb-6">
      {([['salon', 'Serviços do salão'], ['received', 'Notas recebidas do Velour'], ...(config?.can_manage_platform ? [['platform', 'Velour → assinantes']] : [])] as [typeof scope, string][]).map(([key, title]) =>
        <button role="tab" aria-selected={scope === key} className={scope === key ? 'primary-button' : 'secondary-button'} key={key} disabled={busy} onClick={() => switchScope(key)}>{title}</button>)}
    </div>}
    {error && <p role="alert" className="text-danger border border-danger/30 rounded-lg p-3 mb-4">{error}</p>}
    {message && <p role="status" className="text-gold mb-4">{message}</p>}
    {loading ? <p role="status" className="text-muted">Carregando documentos…</p> : <div className="space-y-5">
      {!enabled && <Card><p className="text-muted">Emissão demonstrativa desativada. Os documentos existentes continuam disponíveis para consulta.</p></Card>}
      {scope !== 'received' && <Card>
        <div className="flex flex-wrap justify-between gap-4 items-center"><div><h2 className="text-cream font-medium">Cadastro fiscal {platform ? 'do Velour' : 'do salão'}</h2><p className="text-muted text-sm mt-1">{hasProfile ? `${profile.legal_name} · ${profile.tax_id}` : 'Preencha os dados do prestador antes de criar um documento.'}</p></div>
          <button className="secondary-button" disabled={!enabled || busy} onClick={() => setEditingProfile(v => !v)}>{editingProfile ? 'Fechar cadastro' : 'Editar cadastro fiscal'}</button></div>
        {editingProfile && <form className="mt-6 space-y-5" onSubmit={e => { e.preventDefault(); void act(async () => { await fiscalApi.saveProfile(profile, platform); setHasProfile(true); setEditingProfile(false); setMessage('Cadastro fiscal salvo.'); setRevision(v => v + 1) }) }}>
          <PartyFields value={profile} onChange={v => setProfile({ ...profile, ...v })} />
          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="Inscrição municipal (opcional)" required={false} value={profile.municipal_registration} onChange={v => setProfile({ ...profile, municipal_registration: v })} />
            <label className="text-sm text-muted">Regime tributário<select className={`${inputStyle} mt-1.5`} value={profile.tax_regime} onChange={e => setProfile({ ...profile, tax_regime: e.target.value as FiscalProfile['tax_regime'] })}><option value="mei">MEI</option><option value="simples">Simples Nacional</option><option value="normal">Regime normal</option></select></label>
            <Field label="Código de serviço (6 dígitos)" value={profile.service_code} pattern="[0-9]{6}" onChange={v => setProfile({ ...profile, service_code: v })} />
            <Field label="Alíquota de ISS para demonstração (%)" type="number" min="0" max="5" step="0.01" value={profile.iss_rate} onChange={v => setProfile({ ...profile, iss_rate: v })} />
          </div><button className="primary-button" disabled={busy}>Salvar cadastro fiscal</button>
        </form>}
      </Card>}
      {scope !== 'received' && <div className="flex justify-end"><button className="primary-button" disabled={!enabled || !hasProfile || busy} onClick={() => { setCreating(v => !v); setSelected(null) }}><Plus size={16} /> {creating ? 'Fechar novo documento' : 'Novo documento'}</button></div>}
      {creating && hasProfile && <DraftForm initialAppointmentId={appointmentId} key={scope} platform={platform} profile={profile} appointments={appointments} tenants={tenants} busy={busy} submit={body => act(async () => {
        const doc = await fiscalApi.create(body, platform); setCreating(false); setSelected(doc); setEvents(await fiscalApi.events(doc.id, platform)); setRevision(v => v + 1); setMessage('Rascunho criado. Confira os dados antes de emitir a demonstração.')
      })} />}
      <Card><h2 className="text-cream font-medium mb-4">{scope === 'received' ? 'Documentos recebidos' : 'Documentos de serviço'}</h2>
        {documents.length === 0 ? <div className="text-muted py-8 text-center"><FileText size={32} className="mx-auto mb-3" /><p>Nenhum documento nesta página.</p></div> : <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead className="text-muted"><tr><th className="p-3">Documento</th><th>Tomador</th><th>Competência</th><th>Valor</th><th>Situação</th></tr></thead><tbody>{documents.map(doc => <tr key={doc.id} className="border-t border-border text-cream"><td className="p-3"><button className="text-gold hover:underline" disabled={busy} onClick={() => void inspect(doc)}>{doc.number || `Rascunho #${doc.id}`}</button></td><td>{doc.recipient.legal_name}</td><td>{doc.competence}</td><td className="whitespace-nowrap pr-3">{money(doc.amount)}</td><td>{labels[doc.status]}</td></tr>)}</tbody></table></div>}
        <div className="flex gap-3 mt-4"><button className="secondary-button" disabled={offset === 0 || busy} onClick={() => setOffset(v => Math.max(0, v - 50))}>Anterior</button><button className="secondary-button" disabled={documents.length < 50 || busy} onClick={() => setOffset(v => v + 50)}>Próxima</button></div>
      </Card>
      {selected && <Card><div className="flex justify-between gap-3"><h2 className="text-cream font-medium">{selected.number || `Rascunho #${selected.id}`} · {labels[selected.status]}</h2><button className="text-muted" onClick={() => setSelected(null)}>Fechar detalhes</button></div>
        <div className="grid sm:grid-cols-2 gap-5 my-5 text-sm"><div><p className="text-muted">Prestador</p><p className="text-cream">{selected.issuer.legal_name}</p><p className="text-muted">{selected.issuer.tax_id}</p></div><div><p className="text-muted">Tomador</p><p className="text-cream">{selected.recipient.legal_name}</p><p className="text-muted">{selected.recipient.tax_id}</p></div></div>
        <p className="text-cream whitespace-pre-wrap mb-4">{selected.description}</p><p className="text-muted text-sm">Serviço: {money(selected.amount)} · ISS ilustrativo: {money(selected.iss_amount)} ({selected.iss_rate}%)</p>
        {selected.cancellation_reason && <p className="text-muted mt-3">Cancelamento: {selected.cancellation_reason}</p>}
        <div className="flex flex-wrap gap-3 my-5"><button className="secondary-button" disabled={busy} onClick={() => void download(selected)}><Download size={16} /> Baixar demonstrativo</button>
          {scope !== 'received' && enabled && <>
            {selected.status === 'draft' && <button className="primary-button" disabled={busy} onClick={() => void act(async () => { const doc = await fiscalApi.simulate(selected.id, platform); setSelected(doc); setEvents(await fiscalApi.events(doc.id, platform)); setRevision(v => v + 1); setMessage('Emissão simulada concluída. Documento sem validade fiscal.') })}>Emitir demonstração</button>}
            {selected.status !== 'cancelled' && <button className="secondary-button" disabled={busy} onClick={() => setShowCancel(v => !v)}>Cancelar documento</button>}
          </>}
        </div>
        {showCancel && <form className="space-y-3 mb-5" onSubmit={e => { e.preventDefault(); void act(async () => { const doc = await fiscalApi.cancel(selected.id, cancelReason, platform); setSelected(doc); setShowCancel(false); setEvents(await fiscalApi.events(doc.id, platform)); setRevision(v => v + 1); setMessage('Documento demonstrativo cancelado; histórico preservado.') }) }}><label className="block text-muted text-sm">Motivo do cancelamento (mínimo 15 caracteres)<textarea required minLength={15} maxLength={300} className={`${inputStyle} mt-2`} value={cancelReason} onChange={e => setCancelReason(e.target.value)} /></label><button className="secondary-button" disabled={busy}>Confirmar cancelamento demonstrativo</button></form>}
        <h3 className="text-sm text-cream mb-2">Histórico</h3><ol className="space-y-2 text-muted text-sm">{events.map(event => <li key={event.id}>{actionLabels[event.action] || event.action} · {new Date(event.created_at + 'Z').toLocaleString('pt-BR')}</li>)}</ol>
      </Card>}
    </div>}
  </Wrapper>
}

function DraftForm({ platform, profile, appointments, tenants, busy, submit, initialAppointmentId }: {
  initialAppointmentId?: number
  platform: boolean; profile: FiscalProfile; appointments: FiscalAppointment[]; tenants: FiscalTenant[]; busy: boolean
  submit: (body: import('../api/fiscalTypes').FiscalDraft) => Promise<void>
}) {
  const initial = appointments.find(a => a.id === initialAppointmentId)
  const [source, setSource] = useState(initial ? String(initial.id) : '')
  const [recipient, setRecipient] = useState<FiscalParty>({ ...emptyParty, legal_name: initial?.client_name || '' })
  const [description, setDescription] = useState(initial?.service_name || '')
  const [competence, setCompetence] = useState(initial?.competence || new Date().toLocaleDateString('en-CA'))
  const [amount, setAmount] = useState('')
  const [reference, setReference] = useState('')
  const [code, setCode] = useState(profile.service_code)
  const [rate, setRate] = useState(String(profile.iss_rate))
  const appointment = appointments.find(a => a.id === Number(source))
  function choose(value: string) {
    setSource(value)
    if (platform) {
      const tenant = tenants.find(t => t.id === Number(value))
      const p = tenant?.fiscal_profile
      setRecipient(p ? { legal_name: p.legal_name, tax_id: p.tax_id, email: p.email, street: p.street, number: p.number, district: p.district, postal_code: p.postal_code, city: p.city, municipality_code: p.municipality_code, state: p.state } : { ...emptyParty, legal_name: tenant?.name || '' })
      setDescription('Assinatura mensal Velour — demonstração')
    } else {
      const a = appointments.find(item => item.id === Number(value))
      if (a) { setDescription(a.service_name); setCompetence(a.competence); setRecipient({ ...emptyParty, legal_name: a.client_name }) }
    }
  }
  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void submit({ competence, description, service_code: code, iss_rate: Number(rate), recipient,
      ...(platform ? { tenant_id: Number(source), subscription_reference: reference, amount: Number(amount) } : { appointment_id: Number(source) }) })
  }
  return <Card><h2 className="text-cream font-medium mb-5">Preparar documento demonstrativo</h2><form className="space-y-5" onSubmit={onSubmit}>
    <label className="block text-muted text-sm">{platform ? 'Salão assinante' : 'Atendimento concluído'}<select required className={`${inputStyle} mt-1.5`} value={source} onChange={e => choose(e.target.value)}><option value="">Selecione…</option>{platform ? tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>) : appointments.map(a => <option key={a.id} value={a.id}>#{a.id} · {a.client_name} · {a.service_name} · {money(a.amount)}</option>)}</select></label>
    {!platform && appointments.length === 0 && <p className="text-muted text-sm">Conclua um atendimento com valor positivo para criar um documento. Atendimentos com documento existente aparecem no histórico.</p>}
    <div className="grid sm:grid-cols-2 gap-4"><Field label="Competência" type="date" value={competence} onChange={setCompetence} />
      <Field label="Código de serviço (6 dígitos)" value={code} onChange={setCode} pattern="[0-9]{6}" />
      <Field label="ISS ilustrativo (%)" type="number" min="0" max="5" step="0.01" value={rate} onChange={setRate} />
      {platform ? <><Field label="Valor da assinatura (R$)" type="number" min="0.01" step="0.01" value={amount} onChange={setAmount} /><Field label="Referência única da assinatura / período" value={reference} onChange={setReference} pattern="[A-Za-z0-9_.:\-]+" maxLength={100} /></> : <p className="text-cream self-end pb-3">Valor do atendimento: {money(appointment?.amount || 0)}</p>}
    </div>
    <label className="block text-muted text-sm">Descrição do serviço<textarea required minLength={5} maxLength={2000} className={`${inputStyle} mt-1.5`} value={description} onChange={e => setDescription(e.target.value)} /></label>
    <h3 className="text-cream font-medium">Dados do tomador</h3><PartyFields value={recipient} onChange={setRecipient} />
    <p className="text-muted text-xs">O rascunho preserva os dados informados nesta data. Cancelamentos mantêm o histórico e não liberam a origem para nova emissão neste MVP.</p>
    <button className="primary-button" disabled={busy || !source}>Salvar rascunho</button>
  </form></Card>
}
