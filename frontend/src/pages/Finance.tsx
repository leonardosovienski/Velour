import { useEffect, useState, type FormEvent } from 'react'
import { Link, NavLink, useParams, useSearchParams } from 'react-router'
import { ArrowDownLeft, ArrowUpRight, Wallet, Clock3, Plus, RefreshCw, FileText, CreditCard, ShieldCheck } from 'lucide-react'
import { financeApi, fiscalApi, getErrorDetail } from '../api/client'
import type { ExpenseCategory, FinanceOverview, PaymentMethod, Receipt } from '../api/financeTypes'
import { Layout, Card, PageHeader } from '../components/Layout'
import { useAuth } from '../context/useAuth'
import { Fiscal } from './Fiscal'
import { Billing } from './Billing'

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const today = () => new Date().toLocaleDateString('en-CA')
const field = 'w-full mt-2 bg-bg border border-border rounded-lg p-3 text-cream text-sm'
const categories: Record<ExpenseCategory, string> = { rent: 'Aluguel', supplies: 'Produtos e materiais', utilities: 'Contas e serviços', people: 'Equipe', other: 'Outras despesas' }
const methods: Record<PaymentMethod, string> = { pix: 'Pix', cash: 'Dinheiro', debit_card: 'Cartão de débito', credit_card: 'Cartão de crédito', other: 'Outro' }
const docLabels = { draft: 'Rascunho', simulated: 'Emitido · demonstração', cancelled: 'Cancelado' }
const tabs = [['overview', 'Visão geral'], ['receipts', 'Recebimentos'], ['expenses', 'Despesas'], ['documents', 'Documentos fiscais'], ['subscription', 'Assinatura Velour']]

export function Finance({ section: fixedSection }: { section?: string }) {
  const { section: routeSection } = useParams()
  const section = fixedSection || routeSection || 'overview'
  const { user } = useAuth()
  const [params] = useSearchParams()
  const [month, setMonth] = useState(today().slice(0, 7))
  const [operator, setOperator] = useState(false)
  useEffect(() => {
    let active = true
    if (user?.role === 'admin') fiscalApi.config().then(c => { if (active) setOperator(c.can_manage_platform) }).catch(() => {})
    return () => { active = false }
  }, [user?.role])
  const general = ['overview', 'receipts', 'expenses'].includes(section)
  return <Layout>
    <PageHeader title="Financeiro" subtitle="Acompanhe o dinheiro do salão, organize as contas e cuide dos documentos." />
    <nav aria-label="Áreas do financeiro" className="flex gap-1 overflow-x-auto border-b border-border mb-6 pb-1">
      {tabs.map(([key, label]) => <NavLink key={key} to={`/finance/${key}`} className={() => `shrink-0 px-4 py-3 text-sm border-b-2 transition-colors ${section === key ? 'border-gold text-gold bg-gold/5' : 'border-transparent text-muted hover:text-cream'}`}>{label}</NavLink>)}
    </nav>
    {general && (user?.role === 'professional' ? <Card><p className="text-muted">As finanças são gerenciadas pelo administrador ou gerente do salão.</p></Card> : <>
      <div className="flex flex-wrap items-end justify-between gap-4 mb-6"><div><h2 className="font-display text-2xl text-cream">{tabs.find(([key]) => key === section)?.[1]}</h2><p className="text-muted text-sm mt-1">Atendimentos do mês e despesas pelo vencimento.</p></div><label className="text-muted text-sm">Mês de referência<input type="month" required className={`${field} max-w-52`} value={month} onChange={e => { if (e.target.value) setMonth(e.target.value) }} /></label></div>
      <FinanceLedger key={`${section}-${month}`} section={section} month={month} />
    </>)}
    {section === 'documents' && <Fiscal key={params.toString()} embedded fixedScope="salon" appointmentId={Number(params.get('appointment')) || undefined} documentId={Number(params.get('document')) || undefined} />}
    {section === 'subscription' && <div className="space-y-8"><Billing embedded />{user?.role === 'admin' && <Fiscal embedded fixedScope="received" />}</div>}
    {!tabs.some(([key]) => key === section) && <Card><p className="text-muted">Área não encontrada.</p><Link className="text-gold" to="/finance/overview">Voltar à visão geral</Link></Card>}
    {operator && <div className="mt-10 pt-5 border-t border-border"><Link className="inline-flex items-center gap-2 text-muted hover:text-gold text-sm" to="/platform/fiscal"><ShieldCheck size={16} /> Administração Velour · documentos de assinantes</Link></div>}
  </Layout>
}

export function PlatformFiscal() {
  return <Layout><Link className="inline-block mb-5 text-gold text-sm" to="/finance/overview">← Voltar ao financeiro do salão</Link><PageHeader title="Administração Velour" subtitle="Emissão demonstrativa da plataforma para seus assinantes." /><Fiscal embedded fixedScope="platform" /></Layout>
}

function FinanceLedger({ section, month }: { section: string; month: string }) {
  const { user } = useAuth()
  const [data, setData] = useState<FinanceOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [revision, setRevision] = useState(0)
  const [newExpense, setNewExpense] = useState(false)
  const [receipt, setReceipt] = useState<Receipt | null>(null)
  const [method, setMethod] = useState<PaymentMethod>('pix')
  const [filter, setFilter] = useState('all')
  useEffect(() => {
    let active = true
    financeApi.overview(month).then(result => { if (active) { setData(result); setError('') } })
      .catch(err => { if (active) setError(getErrorDetail(err) || 'Não foi possível carregar as finanças.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [month, revision])
  async function act(action: () => Promise<unknown>, success: string) {
    setBusy(true); setError(''); setMessage('')
    try { await action(); setMessage(success); setRevision(v => v + 1); setNewExpense(false); setReceipt(null) }
    catch (err) { setError(getErrorDetail(err) || 'Não foi possível salvar. Confira os dados e tente novamente.') }
    finally { setBusy(false) }
  }
  const filteredReceipts = data?.receipts.filter(r => filter === 'all' || (filter === 'pending' ? r.remaining > 0 : r.remaining === 0)) || []
  return <div className="space-y-5">
    {error && <div role="alert" className="text-danger border border-danger/30 rounded-xl p-4">{error}<button className="ml-4 underline" onClick={() => { setError(''); setRevision(v => v + 1) }}>Tentar novamente</button></div>}
    {message && <p role="status" className="text-gold">{message}</p>}
    {loading && <p role="status" className="text-muted">Carregando finanças…</p>}
    {data && <>
      {section === 'overview' && <>
        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {[{ label: 'Recebido nos atendimentos', value: data.received, icon: ArrowDownLeft, color: 'text-emerald-400' }, { label: 'A receber', value: data.receivable, icon: Clock3, color: 'text-amber-300' }, { label: 'Despesas pagas', value: data.expenses_paid, icon: ArrowUpRight, color: 'text-rose-300' }, { label: 'Saldo dos registros', value: data.balance, icon: Wallet, color: 'text-gold' }].map(({ label, value, icon: Icon, color }) => <Card key={label}><div className="flex justify-between gap-3 text-muted text-xs mb-5"><span>{label}</span><Icon className={color} size={18} /></div><p className={`font-mono text-2xl ${color}`}>{money(value)}</p></Card>)}
        </div>
        <p className="text-muted text-xs">Resumo por mês do atendimento e vencimento da despesa. O saldo corresponde aos recebimentos registrados menos despesas pagas desse grupo; não é saldo bancário nem fluxo por data de pagamento.</p>
        <div className="grid lg:grid-cols-2 gap-5">
          <Card><h3 className="text-cream font-medium mb-4">Para acompanhar</h3><div className="space-y-4"><Link to="/finance/receipts" className="flex justify-between gap-3 text-sm text-muted hover:text-gold"><span>Atendimentos com valor a receber</span><strong className="text-cream">{data.receipts.filter(r => r.remaining > 0).length}</strong></Link><Link to="/finance/expenses" className="flex justify-between gap-3 text-sm text-muted hover:text-gold"><span>Despesas em aberto</span><strong className="text-cream">{money(data.expenses_pending)}</strong></Link><Link to="/finance/documents" className="flex justify-between gap-3 text-sm text-muted hover:text-gold"><span>Atendimentos sem documento</span><strong className="text-cream">{data.receipts.filter(r => !r.document_id && r.amount > 0).length}</strong></Link></div></Card>
          <Card className="border-gold/20 bg-gold/5"><FileText className="text-gold mb-3" size={22} /><h3 className="text-cream font-medium">Do atendimento ao documento</h3><p className="text-muted text-sm my-3">Registre o recebimento e prepare o documento no mesmo fluxo. A situação do pagamento permanece independente da emissão.</p><Link className="text-gold text-sm" to="/finance/receipts">Acompanhar recebimentos →</Link></Card>
        </div>
        <div className="flex flex-wrap gap-3"><Link className="secondary-button" to="/finance/expenses"><Plus size={16} /> Registrar despesa</Link><Link className="secondary-button" to="/finance/subscription"><CreditCard size={16} /> Minha assinatura Velour</Link></div>
      </>}
      {section === 'receipts' && <>
        <div className="flex flex-wrap justify-between gap-3"><label className="text-muted text-sm">Situação do recebimento<select className={field} value={filter} onChange={e => setFilter(e.target.value)}><option value="all">Todos</option><option value="pending">Com valor a receber</option><option value="paid">Quitados / sem saldo</option></select></label><Link className="secondary-button self-end" to="/appointments">Abrir agenda</Link></div>
        <Card><div className="overflow-x-auto"><table className="w-full text-sm text-left min-w-[720px]"><thead className="text-muted"><tr>{['Atendimento', 'Valor / recebido', 'Pagamento', 'Documento fiscal', 'Ações'].map(t => <th key={t} className="pb-4 pr-4" scope="col">{t}</th>)}</tr></thead><tbody className="divide-y divide-border">{filteredReceipts.map(r => <tr key={r.id} className="text-cream"><td className="py-4 pr-4"><strong className="font-medium">{r.client}</strong><p className="text-muted text-xs mt-1">{r.service} · {r.date.split('-').reverse().join('/')}</p></td><td className="pr-4 font-mono">{money(r.amount)}<p className="text-muted text-xs mt-1">Recebido: {money(r.received)}</p></td><td className="pr-4"><span className={r.remaining > 0 ? 'text-amber-300' : 'text-emerald-400'}>{r.remaining > 0 ? `Pendente: ${money(r.remaining)}` : 'Sem saldo a receber'}</span><p className="text-muted text-xs mt-1">{r.payment_method ? methods[r.payment_method] : 'Sem pagamento registrado'}</p></td><td className="pr-4 text-muted">{r.document_status ? docLabels[r.document_status] : 'Sem documento'}</td><td className="py-3"><div className="flex flex-col items-start gap-2">{r.remaining > 0 && <button className="text-gold hover:underline" disabled={busy} onClick={() => { setReceipt(r); setMethod('pix') }}>Registrar recebimento</button>}{user?.role === 'admin' && r.amount > 0 && <Link className="text-gold hover:underline" to={`/finance/documents?${r.document_id ? `document=${r.document_id}` : `appointment=${r.id}`}`}>{r.document_id ? 'Ver documento' : 'Preparar documento'}</Link>}</div></td></tr>)}</tbody></table></div>{filteredReceipts.length === 0 && <p className="text-muted text-center py-10">{data.receipts.length === 0 ? 'Nenhum atendimento concluído neste mês.' : 'Nenhum recebimento corresponde ao filtro.'}</p>}</Card>
        {receipt && <Card><h3 className="text-cream font-medium">Registrar recebimento · {receipt.client}</h3><p className="text-muted text-sm mt-2">Confirmar o recebimento integral do saldo de {money(receipt.remaining)}. Este registro não realiza cobrança nem transferência.</p><form className="mt-4 space-y-4" onSubmit={e => { e.preventDefault(); void act(() => financeApi.settle(receipt.id, method), 'Recebimento registrado. O documento fiscal não foi alterado.') }}><label className="text-muted text-sm">Forma do recebimento<select className={field} value={method} onChange={e => setMethod(e.target.value as PaymentMethod)}>{Object.entries(methods).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label><div className="flex gap-3"><button className="primary-button" disabled={busy}>Confirmar recebimento</button><button type="button" className="secondary-button" disabled={busy} onClick={() => setReceipt(null)}>Voltar</button></div></form></Card>}
      </>}
      {section === 'expenses' && <>
        <div className="flex flex-wrap justify-between items-center gap-3"><p className="text-muted text-sm">Em aberto: <span className="text-cream">{money(data.expenses_pending)}</span></p><button className="primary-button" disabled={busy} onClick={() => setNewExpense(v => !v)}><Plus size={16} /> {newExpense ? 'Fechar formulário' : 'Nova despesa'}</button></div>
        {newExpense && <ExpenseForm month={month} busy={busy} submit={body => act(() => financeApi.addExpense(body), 'Despesa salva.')} />}
        <Card>{data.expenses.length === 0 ? <div className="py-10 text-center"><Wallet className="mx-auto text-muted mb-3" /><p className="text-cream">Organize as saídas do salão</p><p className="text-muted text-sm mt-2">Cadastre aluguel, produtos e contas para acompanhar o que já foi pago e o que falta pagar.</p></div> : <div className="overflow-x-auto"><table className="w-full text-sm text-left min-w-[560px]"><thead className="text-muted"><tr>{['Despesa', 'Vencimento', 'Valor', 'Situação'].map(t => <th scope="col" className="pb-4" key={t}>{t}</th>)}</tr></thead><tbody className="divide-y divide-border">{data.expenses.map(e => <tr key={e.id} className="text-cream"><td className="py-4 pr-4">{e.description}<p className="text-muted text-xs mt-1">{categories[e.category]}</p></td><td>{e.due_date.split('-').reverse().join('/')}</td><td className="font-mono">{money(e.amount)}</td><td>{e.paid_on ? <span className="text-emerald-400">Paga · {e.paid_on.split('-').reverse().join('/')}</span> : <button className="text-gold hover:underline" disabled={busy} onClick={() => void act(() => financeApi.payExpense(e.id, today()), 'Despesa marcada como paga hoje.')}>Registrar pagamento hoje</button>}</td></tr>)}</tbody></table></div>}</Card>
      </>}
      <button className="text-muted hover:text-gold text-sm inline-flex gap-2 items-center" disabled={busy} onClick={() => setRevision(v => v + 1)}><RefreshCw size={14} /> Atualizar registros</button>
    </>}
  </div>
}

function ExpenseForm({ month, busy, submit }: { month: string; busy: boolean; submit: (body: import('../api/financeTypes').ExpenseInput) => Promise<void> }) {
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState<ExpenseCategory>('other')
  const [amount, setAmount] = useState('')
  const [due, setDue] = useState(month === today().slice(0, 7) ? today() : `${month}-01`)
  const [paid, setPaid] = useState('')
  function save(e: FormEvent) { e.preventDefault(); void submit({ description, category, amount: Number(amount), due_date: due, paid_on: paid || null }) }
  return <Card><form onSubmit={save} className="space-y-5"><h3 className="text-cream font-medium">Nova despesa</h3><div className="grid sm:grid-cols-2 gap-4">
    <label className="text-muted text-sm">Descrição<input className={field} required minLength={3} maxLength={200} value={description} onChange={e => setDescription(e.target.value)} /></label>
    <label className="text-muted text-sm">Categoria<select className={field} value={category} onChange={e => setCategory(e.target.value as ExpenseCategory)}>{Object.entries(categories).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
    <label className="text-muted text-sm">Valor (R$)<input className={field} type="number" min="0.01" step="0.01" max="9999999999.99" required value={amount} onChange={e => setAmount(e.target.value)} /></label>
    <label className="text-muted text-sm">Vencimento<input className={field} type="date" required value={due} onChange={e => setDue(e.target.value)} /></label>
    <label className="text-muted text-sm">Data do pagamento (opcional)<input className={field} type="date" max={today()} value={paid} onChange={e => setPaid(e.target.value)} /><span className="block text-xs mt-2">Deixe em branco se ainda não pagou.</span></label>
  </div><button className="primary-button" disabled={busy}>Salvar despesa</button></form></Card>
}
