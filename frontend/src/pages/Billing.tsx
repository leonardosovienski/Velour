import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { Download, ExternalLink, RefreshCw, CheckCircle2, Clock3 } from 'lucide-react'
import { billingApi, tenantsApi, getErrorDetail } from '../api/client'
import type { BillingStatus } from '../api/types'
import { useAuth } from '../context/useAuth'
import { Layout, Card, PageHeader } from '../components/Layout'
import { FormError } from '../components/AuthShell'
import { PageSpinner } from '../components/Spinner'

const statusLabels: Record<string, string> = { trialing: 'Período de teste', active: 'Ativa', past_due: 'Pagamento pendente', canceled: 'Cancelada', cancelled: 'Cancelada', unpaid: 'Pagamento não realizado', incomplete: 'Aguardando pagamento', incomplete_expired: 'Pagamento expirado', paused: 'Pausada', expired: 'Período de teste encerrado', unsupported_plan: 'Plano indisponível' }

function dateLabel(value: string | null) {
  if (!value) return 'Não informado'
  const date = new Date(value.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`)
  return Number.isNaN(date.getTime()) ? 'Não informado' : date.toLocaleDateString('pt-BR')
}

export function Billing() {
  const { user } = useAuth()
  const [params] = useSearchParams()
  const [status, setStatus] = useState<BillingStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const canManage = user?.role === 'admin' && status?.can_manage_billing

  async function refresh() {
    setLoading(true)
    setError('')
    try { setStatus(await billingApi.status()) }
    catch (err) { setError(getErrorDetail(err) || 'Não foi possível consultar sua assinatura. Tente novamente.') }
    finally { setLoading(false) }
  }

  useEffect(() => { void refresh() }, [])

  async function openBilling(action: 'checkout' | 'portal') {
    setBusy(action)
    setError('')
    try {
      const { url } = await billingApi[action]()
      const destination = new URL(url)
      // Billing links are issued by our API; never execute a non-HTTPS URL.
      if (destination.protocol !== 'https:') throw new Error('Invalid billing URL')
      window.location.assign(destination.href)
    } catch (err) {
      setError(getErrorDetail(err) || 'Não foi possível abrir o pagamento. Tente novamente em instantes.')
    } finally { setBusy('') }
  }

  async function exportData() {
    setBusy('export')
    setError('')
    setMessage('')
    try {
      const blob = await tenantsApi.export()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `velour-dados-${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(link)
      link.click()
      link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      setMessage('Exportação concluída. Guarde o arquivo em um local seguro: ele contém dados dos seus clientes.')
    } catch (err) { setError(getErrorDetail(err) || 'Não foi possível exportar os dados. Tente novamente.') }
    finally { setBusy('') }
  }

  return (
    <Layout>
      <PageHeader title="Conta e assinatura" subtitle="Acompanhe seu plano e mantenha seu salão em dia." action={<button className="secondary-button" disabled={loading || !!busy} onClick={refresh}><RefreshCw size={15} /> Atualizar status</button>} />
      <div className="space-y-5">
        {params.get('welcome') === '1' && <Card className="border-gold/30"><h2 className="text-cream font-medium mb-2">Seu salão está pronto para começar</h2><p className="text-muted text-sm">Cadastre os profissionais, adicione os serviços e marque seu primeiro atendimento.</p><div className="flex gap-3 flex-wrap mt-4"><Link className="secondary-button" to="/professionals">1. Profissionais</Link><Link className="secondary-button" to="/services">2. Serviços</Link><Link className="secondary-button" to="/appointments">3. Agenda</Link></div></Card>}
        {(params.get('checkout') === 'success' || params.get('success') === 'true') && <p role="status" className="bg-gold/10 border border-gold/20 rounded-xl p-4 text-sm text-cream">Recebemos seu retorno do pagamento. A confirmação pode levar alguns instantes. Atualize o status para conferir a ativação.</p>}
        {params.get('checkout') === 'cancelled' && <p role="status" className="text-muted text-sm">O pagamento não foi concluído. Você pode retomá-lo quando quiser.</p>}
        <FormError message={error} />
        {message && <p role="status" className="text-cream text-sm">{message}</p>}
        {loading ? <PageSpinner /> : status && <>
          <Card>
            <div className="flex gap-4 items-start">
              {status.access_allowed ? <CheckCircle2 className="text-gold shrink-0" size={26} /> : <Clock3 className="text-gold shrink-0" size={26} />}
              <div className="min-w-0 flex-1"><h2 className="font-display text-2xl text-cream break-words">{status.tenant_name}</h2><p className="text-gold text-sm mt-1">{statusLabels[status.subscription_status] || 'Consulte sua assinatura'}</p></div>
            </div>
            <dl className="grid sm:grid-cols-2 gap-5 mt-6 text-sm">
              <div><dt className="text-muted mb-1">Acesso ao sistema</dt><dd className="text-cream">{status.access_allowed ? 'Liberado' : 'Aguardando regularização'}</dd></div>
              {status.subscription_status === 'trialing' ? <div><dt className="text-muted mb-1">Fim do período de teste</dt><dd className="text-cream">{dateLabel(status.trial_ends_at)}</dd></div> : status.current_period_end && <div><dt className="text-muted mb-1">Fim do período atual</dt><dd className="text-cream">{dateLabel(status.current_period_end)}</dd></div>}
            </dl>
            {!status.access_allowed && <p role="alert" className="text-cream text-sm mt-5">{canManage ? 'Regularize a assinatura para voltar a usar a agenda e os demais recursos. A exportação dos dados continua disponível.' : 'Peça ao administrador do salão para regularizar a assinatura e liberar o acesso.'}</p>}
            {canManage ? <div className="mt-6 space-y-3">
              {status.configured ? <div className="flex flex-wrap gap-3">
                {['trialing', 'canceled', 'cancelled', 'incomplete_expired', 'expired'].includes(status.subscription_status) && <button className="primary-button" disabled={!!busy} onClick={() => openBilling('checkout')}><ExternalLink size={16} /> {busy === 'checkout' ? 'Abrindo…' : 'Assinar Velour'}</button>}
                {status.has_billing_customer && <button className="secondary-button" disabled={!!busy} onClick={() => openBilling('portal')}><ExternalLink size={16} /> {busy === 'portal' ? 'Abrindo…' : 'Gerenciar pagamentos e cancelamento'}</button>}
              </div> : <p className="text-muted text-sm">O pagamento online está temporariamente indisponível. Entre em contato com a equipe responsável pelo Velour.</p>}
              <p className="text-muted text-xs">O preço, a periodicidade e as condições serão exibidos antes da confirmação do pagamento.</p>
            </div> : <p className="text-muted text-sm mt-5">A assinatura é gerenciada pelo administrador do salão.</p>}
          </Card>
          {user?.role === 'admin' && <Card><h2 className="text-cream font-medium">Seus dados</h2><p className="text-muted text-sm mt-2 mb-4">Baixe os registros do salão em JSON para portabilidade. O arquivo contém informações pessoais de clientes e deve ser compartilhado somente com pessoas autorizadas.</p><button className="secondary-button" disabled={!!busy} onClick={exportData}><Download size={16} /> {busy === 'export' ? 'Preparando arquivo…' : 'Exportar dados do salão'}</button></Card>}
          {status.access_allowed && <Link className="text-gold text-sm inline-block" to="/">Voltar ao painel</Link>}
        </>}
      </div>
    </Layout>
  )
}
