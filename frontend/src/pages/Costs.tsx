import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Download, Pencil, TriangleAlert } from 'lucide-react'
import { costsApi, getErrorDetail } from '../api/client'
import type { CostCategory, CostLine, CostReport } from '../api/financeTypes'
import { Card } from '../components/Layout'

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const percent = (n: number | null) => n === null ? '—' : n.toLocaleString('pt-BR', { style: 'percent', maximumFractionDigits: 1 })
const monthLabel = (m: string) => `${m.slice(5)}/${m.slice(0, 4)}`
const field = 'w-full mt-2 bg-bg border border-border rounded-lg p-3 text-cream text-sm'
const statusText: Record<CostLine['status'], string> = { within: 'Dentro do orçamento', over: 'Acima do orçamento', no_budget: 'Sem orçamento' }
const statusColor: Record<CostLine['status'], string> = { within: 'text-emerald-400', over: 'text-rose-300', no_budget: 'text-muted' }

function Table({ caption, headers, minWidth = 'min-w-[560px]', children }: { caption: string; headers: string[]; minWidth?: string; children: ReactNode }) {
  return <div className="overflow-x-auto"><table className={`w-full text-sm text-left ${minWidth}`}>
    <caption className="sr-only">{caption}</caption>
    <thead className="text-muted"><tr>{headers.map(t => <th key={t} scope="col" className="pb-3 pr-3 font-normal">{t}</th>)}</tr></thead>
    <tbody className="divide-y divide-border">{children}</tbody>
  </table></div>
}

export function Costs({ month }: { month: string }) {
  const [data, setData] = useState<CostReport | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(false)
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    let active = true
    costsApi.report(month).then(result => { if (active) { setData(result); setError('') } })
      .catch(err => { if (active) setError(getErrorDetail(err) || 'Não foi possível carregar a gestão de custos.') })
    return () => { active = false }
  }, [month, revision])
  async function download() {
    setBusy(true); setError(''); setMessage('')
    try {
      const url = URL.createObjectURL(await costsApi.download(month))
      const link = document.createElement('a'); link.href = url; link.download = `velour-custos-${month}.csv`
      document.body.appendChild(link); link.click(); link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) { setError(getErrorDetail(err) || 'Não foi possível gerar o arquivo.') }
    finally { setBusy(false) }
  }
  async function saveBudget(items: { category: CostCategory; amount: number }[]) {
    setBusy(true); setError(''); setMessage('')
    try { await costsApi.saveBudget(month, items); setEditing(false); setMessage('Orçamento do mês salvo.'); setRevision(v => v + 1) }
    catch (err) { setError(getErrorDetail(err) || 'Não foi possível salvar o orçamento. Confira os valores.') }
    finally { setBusy(false) }
  }
  if (!data) return error
    ? <div role="alert" className="text-danger border border-danger/30 rounded-xl p-4">{error}<button className="ml-4 underline" onClick={() => { setError(''); setRevision(v => v + 1) }}>Tentar novamente</button></div>
    : <p role="status" className="text-muted">Carregando gestão de custos…</p>
  const s = data.summary
  const peak = Math.max(1, ...data.history.map(h => Math.max(h.revenue, h.variable_costs + h.fixed_costs)))
  const indicators = [
    { label: 'Receita do mês', value: money(s.revenue), hint: `${s.appointments} atendimento${s.appointments === 1 ? '' : 's'} concluído${s.appointments === 1 ? '' : 's'}` },
    { label: 'Custos variáveis', value: money(s.variable_costs), hint: 'Insumos, comissões e ISS' },
    { label: 'Margem de contribuição', value: money(s.contribution_margin), hint: `${percent(s.contribution_margin_ratio)} da receita` },
    { label: 'Custos fixos', value: money(s.fixed_costs), hint: 'Despesas pelo vencimento' },
    { label: 'Resultado do mês', value: money(s.result), hint: s.result < 0 ? 'Prejuízo no período' : 'Lucro no período', tone: s.result < 0 ? 'text-rose-300' : 'text-emerald-400' },
    { label: 'Ponto de equilíbrio', value: s.break_even_revenue === null ? 'Não calculável' : money(s.break_even_revenue), hint: s.break_even_appointments === null ? 'Sem margem positiva no mês' : `Cerca de ${s.break_even_appointments} atendimento${s.break_even_appointments === 1 ? '' : 's'}` },
    { label: 'Margem de segurança', value: percent(s.safety_margin), hint: 'Quanto a receita pode cair até o equilíbrio' },
    { label: 'Ticket médio', value: s.average_ticket === null ? '—' : money(s.average_ticket), hint: s.cost_per_appointment === null ? 'Sem atendimentos' : `Custo por atendimento: ${money(s.cost_per_appointment)}` },
  ]
  return <div className="space-y-5">
    <p className="text-muted text-sm">{data.notice}</p>
    {error && <div role="alert" className="text-danger border border-danger/30 rounded-xl p-4">{error}</div>}
    {message && <p role="status" className="text-gold">{message}</p>}
    <div className="flex flex-wrap gap-3">
      <button className="secondary-button" disabled={busy} onClick={() => void download()}><Download size={16} /> Baixar planilha (CSV)</button>
      <button className="secondary-button" disabled={busy} aria-expanded={editing} onClick={() => setEditing(v => !v)}><Pencil size={16} /> {editing ? 'Fechar orçamento' : 'Definir orçamento do mês'}</button>
    </div>

    <section aria-labelledby="cost-indicators"><h3 id="cost-indicators" className="sr-only">Indicadores do mês</h3>
      <ul className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">{indicators.map(item => <li key={item.label}><Card className="h-full"><p className="text-muted text-xs">{item.label}</p><p className={`font-mono text-2xl mt-3 ${item.tone || 'text-cream'}`}>{item.value}</p><p className="text-muted text-xs mt-2">{item.hint}</p></Card></li>)}</ul>
    </section>

    <section aria-labelledby="cost-alerts"><Card>
      <h3 id="cost-alerts" className="text-cream font-medium mb-3">Alertas de custo</h3>
      {data.alerts.length === 0 ? <p className="text-muted text-sm">Nenhum alerta de custo neste mês.</p> : <ul className="space-y-2">{data.alerts.map(alert => <li key={alert.message} className={`flex gap-2 text-sm ${alert.level === 'danger' ? 'text-rose-300' : 'text-amber-300'}`}><TriangleAlert size={16} aria-hidden="true" className="shrink-0 mt-0.5" /><span><span className="sr-only">{alert.level === 'danger' ? 'Crítico: ' : 'Atenção: '}</span>{alert.message}</span></li>)}</ul>}
    </Card></section>

    {editing && <BudgetForm lines={data.lines} busy={busy} submit={saveBudget} cancel={() => setEditing(false)} />}

    <section aria-labelledby="cost-budget"><Card>
      <div className="flex flex-wrap justify-between gap-2 mb-4"><h3 id="cost-budget" className="text-cream font-medium">Orçado × realizado</h3>{data.budget_total !== null && <p className="text-muted text-sm">Orçamento total: <span className="text-cream font-mono">{money(data.budget_total)}</span></p>}</div>
      <Table caption="Custos realizados comparados ao orçamento do mês" headers={['Linha de custo', 'Realizado', 'Orçado', 'Variação', 'Situação']} minWidth="min-w-[640px]">
        {data.lines.map(line => <tr key={line.category} className="text-cream">
          <td className="py-3 pr-3">{line.label}<p className="text-muted text-xs mt-1">{line.kind === 'variable' ? 'Variável' : 'Fixo'}</p></td>
          <td className="pr-3 font-mono">{money(line.actual)}</td>
          <td className="pr-3 font-mono">{line.budget === null ? '—' : money(line.budget)}</td>
          <td className="pr-3 font-mono">{line.variance === null ? '—' : money(line.variance)}</td>
          <td className="pr-3"><span className={statusColor[line.status]}>{statusText[line.status]}</span>{line.consumed_ratio !== null && <div aria-hidden="true" className="mt-2 h-1.5 w-28 rounded bg-border overflow-hidden"><div className={`h-full ${line.status === 'over' ? 'bg-rose-300' : 'bg-emerald-400'}`} style={{ width: `${Math.min(100, line.consumed_ratio * 100)}%` }} /></div>}</td>
        </tr>)}
      </Table>
    </Card></section>

    <section aria-labelledby="cost-history"><Card>
      <h3 id="cost-history" className="text-cream font-medium mb-1">Evolução dos últimos seis meses</h3>
      <p className="text-muted text-xs mb-4">Barra dourada: receita. Barra rosa: custos variáveis e fixos.</p>
      <Table caption="Receita, custos e resultado por mês" headers={['Mês', 'Receita', 'Custos', 'Resultado', 'Comparação']} minWidth="min-w-[600px]">
        {data.history.map(h => { const costs = h.variable_costs + h.fixed_costs; return <tr key={h.month} className={h.month === data.month ? 'text-cream font-medium' : 'text-cream'}>
          <td className="py-3 pr-3">{monthLabel(h.month)}</td>
          <td className="pr-3 font-mono">{money(h.revenue)}</td>
          <td className="pr-3 font-mono">{money(costs)}</td>
          <td className={`pr-3 font-mono ${h.result < 0 ? 'text-rose-300' : 'text-emerald-400'}`}>{money(h.result)}</td>
          <td className="w-48" aria-hidden="true"><div className="space-y-1"><div className="h-2 rounded bg-gold" style={{ width: `${(h.revenue / peak) * 100}%` }} /><div className="h-2 rounded bg-rose-300" style={{ width: `${(costs / peak) * 100}%` }} /></div></td>
        </tr> })}
      </Table>
    </Card></section>

    <div className="grid gap-5">
      <section aria-labelledby="cost-services" className="min-w-0"><Card className="h-full">
        <h3 id="cost-services" className="text-cream font-medium mb-4">Margem por serviço</h3>
        {data.services.length === 0 ? <p className="text-muted text-sm py-6 text-center">Nenhum atendimento concluído neste mês.</p> : <Table caption="Receita, custos variáveis e margem de contribuição por serviço" headers={['Serviço', 'Receita', 'Custos variáveis', 'Margem']}>
          {data.services.map(row => <tr key={row.id} className="text-cream"><td className="py-3 pr-3">{row.name}<p className="text-muted text-xs mt-1">{row.category} · {row.appointments} atend.</p></td><td className="pr-3 font-mono">{money(row.revenue)}</td><td className="pr-3 font-mono">{money(row.inputs + row.commissions + row.taxes)}</td><td className={`pr-3 font-mono ${row.contribution_margin < 0 ? 'text-rose-300' : ''}`}>{money(row.contribution_margin)}<p className="text-muted text-xs mt-1">{percent(row.margin_ratio)}</p></td></tr>)}
        </Table>}
      </Card></section>
      <section aria-labelledby="cost-professionals" className="min-w-0"><Card className="h-full">
        <h3 id="cost-professionals" className="text-cream font-medium mb-4">Centros de custo por profissional</h3>
        {data.professionals.length === 0 ? <p className="text-muted text-sm py-6 text-center">Nenhum atendimento concluído neste mês.</p> : <Table caption="Receita, comissões, insumos e margem por profissional" headers={['Profissional', 'Receita', 'Comissões', 'Insumos', 'Margem']}>
          {data.professionals.map(row => <tr key={row.id} className="text-cream"><td className="py-3 pr-3">{row.name}<p className="text-muted text-xs mt-1">Comissão de {percent(row.commission_rate)} · {row.appointments} atend.</p></td><td className="pr-3 font-mono">{money(row.revenue)}</td><td className="pr-3 font-mono">{money(row.commissions)}</td><td className="pr-3 font-mono">{money(row.inputs)}</td><td className={`pr-3 font-mono ${row.contribution_margin < 0 ? 'text-rose-300' : ''}`}>{money(row.contribution_margin)}</td></tr>)}
        </Table>}
      </Card></section>
    </div>

    <section aria-labelledby="cost-standard"><Card>
      <h3 id="cost-standard" className="text-cream font-medium mb-1">Custo-padrão pela ficha técnica</h3>
      <p className="text-muted text-xs mb-4">Quanto cada serviço ativo consome de insumos por execução, com o ISS estimado de {data.iss_rate.toLocaleString('pt-BR')}%. A comissão depende do profissional e fica fora desta margem.</p>
      {data.standard_costs.length === 0 ? <p className="text-muted text-sm py-6 text-center">Nenhum serviço ativo.</p> : <Table caption="Preço, custo-padrão de insumos e margem antes da comissão por serviço" headers={['Serviço', 'Preço', 'Insumos', 'ISS', 'Margem antes da comissão']} minWidth="min-w-[640px]">
        {data.standard_costs.map(row => <tr key={row.id} className="text-cream"><td className="py-3 pr-3">{row.name}<p className="text-muted text-xs mt-1">{row.recipe_items === 0 ? 'Sem ficha técnica' : `${row.recipe_items} insumo${row.recipe_items === 1 ? '' : 's'} · ${percent(row.input_ratio)} do preço`}</p></td><td className="pr-3 font-mono">{money(row.price)}</td><td className="pr-3 font-mono">{money(row.standard_input_cost)}</td><td className="pr-3 font-mono">{money(row.taxes)}</td><td className={`pr-3 font-mono ${row.margin_before_commission <= 0 ? 'text-rose-300' : ''}`}>{money(row.margin_before_commission)}</td></tr>)}
      </Table>}
    </Card></section>
  </div>
}

function BudgetForm({ lines, busy, submit, cancel }: { lines: CostLine[]; busy: boolean; submit: (items: { category: CostCategory; amount: number }[]) => Promise<void>; cancel: () => void }) {
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(lines.map(line => [line.category, line.budget === null ? '' : String(line.budget)])))
  function save(e: FormEvent) {
    e.preventDefault()
    void submit(lines.filter(line => values[line.category] !== '').map(line => ({ category: line.category, amount: Number(values[line.category]) })))
  }
  return <Card><form onSubmit={save} className="space-y-5" aria-labelledby="budget-form-title">
    <div><h3 id="budget-form-title" className="text-cream font-medium">Orçamento do mês</h3><p className="text-muted text-sm mt-1">Defina o limite de cada linha. Deixe em branco a linha sem orçamento. Salvar substitui o orçamento inteiro do mês.</p></div>
    <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">{lines.map(line => <label key={line.category} className="text-muted text-sm">{line.label} (R$)
      <input className={field} type="number" min="0" step="0.01" max="9999999999.99" inputMode="decimal" value={values[line.category]} onChange={e => setValues(v => ({ ...v, [line.category]: e.target.value }))} />
    </label>)}</div>
    <div className="flex gap-3"><button className="primary-button" disabled={busy}>Salvar orçamento</button><button type="button" className="secondary-button" disabled={busy} onClick={cancel}>Cancelar</button></div>
  </form></Card>
}
