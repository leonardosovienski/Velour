import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { tenantsApi, getErrorDetail } from '../api/client'
import type { SignupConfig } from '../api/types'
import { useAuth } from '../context/useAuth'
import { AuthShell, FormError } from '../components/AuthShell'
import { Spinner } from '../components/Spinner'

function legalUrl(value?: string) {
  try {
    const url = new URL(value || '')
    return url.protocol === 'https:' ? url.href : undefined
  } catch { return undefined }
}

export function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [config, setConfig] = useState<SignupConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [accepted, setAccepted] = useState(false)
  const termsUrl = legalUrl(config?.terms_url)
  const privacyUrl = legalUrl(config?.privacy_url)
  const signupAvailable = config?.signup_enabled && termsUrl && privacyUrl

  useEffect(() => {
    let active = true
    tenantsApi.signupConfig().then(data => { if (active) setConfig(data) })
      .catch(() => { if (active) setError('Não foi possível carregar o cadastro. Tente novamente em instantes.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!signupAvailable || !accepted || submitting) return
    if (password !== confirmPassword) { setError('As senhas precisam ser iguais.'); return }
    setError('')
    setSubmitting(true)
    try {
      await signup({ tenant_name: tenantName.trim(), admin_name: name.trim(), admin_email: email.trim(), admin_password: password, accepted_terms: accepted })
      navigate('/billing?welcome=1', { replace: true })
    } catch (err) {
      setError(getErrorDetail(err) || 'Não foi possível criar sua conta. Tente novamente.')
    } finally { setSubmitting(false) }
  }

  return (
    <AuthShell title="Seu salão, mais organizado" subtitle={config ? `Experimente o Velour por ${config.trial_days} dias. Sem cartão para começar.` : 'Crie sua conta e comece a organizar seu negócio.'}>
      {loading ? <div role="status" aria-label="Carregando cadastro"><Spinner /></div> : !signupAvailable ? (
        <div className="space-y-4"><FormError message={error} /><p className="text-muted text-sm">Novos cadastros estão temporariamente indisponíveis. Tente novamente mais tarde.</p></div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div><label htmlFor="signup-salon" className="field-label">Nome do salão</label><input id="signup-salon" autoComplete="organization" required minLength={2} maxLength={120} value={tenantName} onChange={e => setTenantName(e.target.value)} /></div>
          <div><label htmlFor="signup-name" className="field-label">Seu nome</label><input id="signup-name" autoComplete="name" required minLength={2} maxLength={120} value={name} onChange={e => setName(e.target.value)} /></div>
          <div><label htmlFor="signup-email" className="field-label">Email de acesso</label><input id="signup-email" type="email" autoComplete="username" required value={email} onChange={e => setEmail(e.target.value)} /></div>
          <div><label htmlFor="signup-password" className="field-label">Senha</label><input id="signup-password" type="password" autoComplete="new-password" aria-describedby="signup-password-hint" required minLength={12} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} /><p id="signup-password-hint" className="text-muted text-xs mt-1.5">Use entre 12 e 128 caracteres.</p></div>
          <div><label htmlFor="signup-confirm" className="field-label">Confirmar senha</label><input id="signup-confirm" type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} /></div>
          <label className="flex gap-3 items-start text-sm text-muted"><input type="checkbox" className="mt-1 shrink-0" required checked={accepted} onChange={e => setAccepted(e.target.checked)} /><span>Li e aceito os <a className="text-gold underline" target="_blank" rel="noopener noreferrer" href={termsUrl}>Termos de Uso</a> e a <a className="text-gold underline" target="_blank" rel="noopener noreferrer" href={privacyUrl}>Política de Privacidade</a>.</span></label>
          <FormError message={error} />
          <button className="primary-button w-full" disabled={submitting || !accepted} type="submit">{submitting ? 'Criando sua conta…' : 'Começar período de teste'}</button>
        </form>
      )}
      <p className="text-muted text-sm text-center mt-6">Já tem uma conta? <Link to="/login" className="text-gold">Entrar</Link></p>
    </AuthShell>
  )
}
