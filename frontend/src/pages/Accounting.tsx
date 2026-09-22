import { useEffect, useState } from 'react'
import { Download, FileText, Scale } from 'lucide-react'
import { accountingApi, getErrorDetail } from '../api/client'
import type { AccountingReport } from '../api/financeTypes'
import { Card } from '../components/Layout'

const money = (n: number) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const brDate = (d: string) => d.split('-').reverse().join('/')

export function Accounting({ month }: { month: string }) {
  const [data, setData] = useState<AccountingReport | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    let active = true
    accountingApi.report(month).then(result => { if (active) { setData(result); setError('') } })
      .catch(err => { if (active) setError(getErrorDetail(err) || 'Não foi possível carregar a contabilidade.') })
    return () => { active = false }
  }, [month])
  async function download(format: 'txt' | 'pdf') {
    setBusy(true); setError('')
    try {
      const blob = await accountingApi.download(month, format)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a'); link.href = url; link.download = `velour-contabil-${month}.${format}`
      document.body.appendChild(link); link.click(); link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) { setError(getErrorDetail(err) || 'Não foi possível gerar o arquivo.') }
    finally { setBusy(false) }
  }
  if (error) return <div role="alert" className="text-danger border border-danger/30 rounded-xl p-4">{error}</div>
  if (!data) return <p role="status" className="text-muted">Carregando contabilidade…</p>
  const balanced = data.total_debit === data.total_credit
  return <div className="space-y-5">
    <p className="text-amber-300 text-sm border border-amber-300/30 rounded-xl p-4">{data.notice}</p>
    <div className="flex flex-wrap gap-3">
      <button className="primary-button" disabled={busy} onClick={() => void download('pdf')}><Download size={16} /> Baixar PDF</button>
      <button className="secondary-button" disabled={busy} onClick={() => void download('txt')}><FileText size={16} /> Baixar TXT</button>
    </div>
    <div className="grid lg:grid-cols-2 gap-5">
      <Card>
        <h3 className="text-cream font-medium mb-4">DRE · Demonstração do resultado</h3>
        <table className="w-full text-sm"><tbody>{data.dre.map(row => <tr key={row.label} className={row.level ? 'text-muted' : 'text-cream font-medium border-t border-border'}>
          <td className={`py-2 ${row.level ? 'pl-4' : ''}`}>{row.label}</td>
          <td className={`py-2 text-right font-mono ${row.label === 'Resultado do período' ? (row.value < 0 ? 'text-rose-300' : 'text-emerald-400') : ''}`}>{money(row.value)}</td>
        </tr>)}</tbody></table>
        <p className="text-muted text-xs mt-4">ISS estimado com a alíquota do cadastro fiscal ({data.iss_rate.toFixed(2)}%). Receitas e comissões pela data do atendimento; despesas pelo vencimento.</p>
      </Card>
      <Card>
        <div className="flex justify-between items-center mb-4"><h3 className="text-cream font-medium">Balancete de verificação</h3><span className={`inline-flex items-center gap-1 text-xs ${balanced ? 'text-emerald-400' : 'text-danger'}`}><Scale size={14} /> {balanced ? 'Débitos = créditos' : 'Diferença entre débitos e créditos'}</span></div>
        {data.trial_balance.length === 0 ? <p className="text-muted text-sm py-6 text-center">Sem movimento neste mês.</p> : <div className="overflow-x-auto"><table className="w-full text-sm min-w-[460px]"><thead className="text-muted text-left"><tr>{['Conta', 'Débitos', 'Créditos', 'Saldo'].map(t => <th key={t} scope="col" className="pb-3">{t}</th>)}</tr></thead>
          <tbody className="divide-y divide-border">{data.trial_balance.map(row => <tr key={row.code} className="text-cream"><td className="py-2 pr-3"><span className="text-muted font-mono text-xs">{row.code}</span> {row.name}</td><td className="font-mono">{money(row.debit)}</td><td className="font-mono">{money(row.credit)}</td><td className="font-mono">{money(row.balance)}</td></tr>)}</tbody>
          <tfoot><tr className="text-cream font-medium border-t border-border"><td className="pt-3">Totais</td><td className="pt-3 font-mono">{money(data.total_debit)}</td><td className="pt-3 font-mono">{money(data.total_credit)}</td><td /></tr></tfoot></table></div>}
      </Card>
    </div>
    <Card>
      <h3 className="text-cream font-medium mb-4">Livro diário · lançamentos simulados</h3>
      {data.entries.length === 0 ? <p className="text-muted text-sm py-6 text-center">Nenhum lançamento neste mês. Conclua atendimentos ou registre despesas para gerar lançamentos.</p> : <div className="overflow-x-auto"><table className="w-full text-sm text-left min-w-[640px]"><thead className="text-muted"><tr>{['Data', 'Histórico', 'Débito', 'Crédito', 'Valor'].map(t => <th key={t} scope="col" className="pb-3 pr-3">{t}</th>)}</tr></thead>
        <tbody className="divide-y divide-border">{data.entries.map((row, i) => <tr key={i} className="text-cream"><td className="py-2 pr-3">{brDate(row.date)}</td><td className="pr-3">{row.history}</td><td className="pr-3 font-mono text-xs">{row.debit}</td><td className="pr-3 font-mono text-xs">{row.credit}</td><td className="font-mono">{money(row.amount)}</td></tr>)}</tbody></table></div>}
    </Card>
  </div>
}
