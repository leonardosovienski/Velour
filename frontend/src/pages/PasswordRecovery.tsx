import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router'
import { authApi, getErrorDetail, getErrorStatus } from '../api/client'
import { AuthShell, FormError } from '../components/AuthShell'

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [pending, setPending] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: FormEvent) {
    e.preventDefault()
    setPending(true)
    setError('')
    try { await authApi.forgotPassword(email.trim()); setSent(true) }
    catch (err) { setError(getErrorStatus(err) === 429 ? 'Aguarde alguns minutos antes de solicitar outro link.' : 'Não foi possível enviar a solicitação. Tente novamente.') }
    finally { setPending(false) }
  }
  return (
    <AuthShell title="Recuperar acesso" subtitle="Enviaremos um link para você criar uma nova senha.">
      {sent ? <p role="status" className="text-cream text-sm leading-relaxed">Se este email estiver cadastrado, você receberá as instruções de recuperação. Confira também a pasta de spam.</p> : (
        <form onSubmit={submit} className="space-y-4">
          <div><label className="field-label" htmlFor="recovery-email">Email de acesso</label><input id="recovery-email" type="email" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <FormError message={error} /><button type="submit" disabled={pending} className="primary-button w-full">{pending ? 'Enviando…' : 'Enviar link de recuperação'}</button>
        </form>
      )}
      <Link className="text-gold text-sm block mt-6 text-center" to="/login">Voltar para entrar</Link>
    </AuthShell>
  )
}

export function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [pending, setPending] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: FormEvent) {
    e.preventDefault()
    if (password !== confirmPassword) { setError('As senhas precisam ser iguais.'); return }
    setPending(true)
    setError('')
    try { await authApi.resetPassword(token, password); sessionStorage.removeItem('access_token'); window.dispatchEvent(new Event('velour:session-expired')); setDone(true) }
    catch (err) { setError(getErrorDetail(err) || 'Não foi possível alterar a senha. Solicite um novo link e tente novamente.') }
    finally { setPending(false) }
  }
  return (
    <AuthShell title="Criar nova senha" subtitle="Escolha uma senha exclusiva para sua conta.">
      {done ? <p role="status" className="text-cream text-sm">Senha alterada. Entre com sua nova senha.</p> : !token ? <p role="alert" className="text-red-300 text-sm">O link de recuperação está incompleto. Solicite um novo link.</p> : (
        <form onSubmit={submit} className="space-y-4">
          <div><label htmlFor="new-password" className="field-label">Nova senha</label><input id="new-password" type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} aria-describedby="password-hint" /><p id="password-hint" className="text-muted text-xs mt-1.5">Use entre 12 e 128 caracteres.</p></div>
          <div><label htmlFor="confirm-password" className="field-label">Confirmar nova senha</label><input id="confirm-password" type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} /></div>
          <FormError message={error} /><button type="submit" disabled={pending} className="primary-button w-full">{pending ? 'Salvando…' : 'Salvar nova senha'}</button>
        </form>
      )}
      {!done && <Link className="text-gold text-sm block mt-6 text-center" to="/forgot-password">Solicitar novo link</Link>}
      <Link className="text-gold text-sm block mt-4 text-center" to="/login">Voltar para entrar</Link>
    </AuthShell>
  )
}
