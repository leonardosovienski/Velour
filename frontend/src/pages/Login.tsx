import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../context/useAuth'
import { getErrorStatus } from '../api/client'
import { AuthShell, FormError } from '../components/AuthShell'

export function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (err) {
      const status = getErrorStatus(err)
      setError(status === 401 ? 'Email ou senha incorretos.' : status === 429
        ? 'Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.'
        : 'Não foi possível entrar. Verifique sua conexão e tente novamente.')
    } finally { setLoading(false) }
  }

  return (
    <AuthShell title="Bem-vindo de volta" subtitle="Acesse a agenda e cuide do seu negócio.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="login-email" className="field-label">Email</label>
          <input id="login-email" type="email" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} required autoFocus />
        </div>
        <div>
          <label htmlFor="login-password" className="field-label">Senha</label>
          <input id="login-password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        <Link className="text-gold text-sm block text-right" to="/forgot-password">Esqueci minha senha</Link>
        <FormError message={error} />
        <button type="submit" disabled={loading} className="primary-button w-full">{loading ? 'Entrando…' : 'Entrar'}</button>
      </form>
      <p className="text-center text-muted text-sm mt-6">Seu salão ainda não está no Velour? <Link className="text-gold" to="/signup">Criar conta</Link></p>
    </AuthShell>
  )
}
