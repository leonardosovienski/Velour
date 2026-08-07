import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { useAuth } from '../context/useAuth'
import { getErrorStatus } from '../api/client'
import { Spinner } from '../components/Spinner'

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
      navigate('/')
    } catch (err) {
      if (getErrorStatus(err) === 401) {
        setError('Email ou senha incorretos.')
      } else {
        setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando na porta 8000.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="font-display text-5xl font-semibold text-gold tracking-widest mb-2">
            VELOUR
          </div>
          <div className="text-muted text-xs uppercase tracking-[0.3em]">
            Gestão de Salão Premium
          </div>
        </div>

        {/* Card */}
        <div className="bg-surface border border-border rounded-2xl p-8 shadow-2xl">
          <h2 className="font-display text-xl text-cream font-medium mb-6">Acesso restrito</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-muted text-xs uppercase tracking-wider block mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="text-muted text-xs uppercase tracking-wider block mb-1.5">Senha</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="bg-danger/10 border border-danger/30 text-red-400 text-sm rounded-lg px-4 py-3">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gold hover:bg-gold/90 text-bg font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 mt-2 disabled:opacity-60"
            >
              {loading ? <Spinner size={18} /> : 'Entrar'}
            </button>
          </form>
        </div>

        <p className="text-center text-muted text-xs mt-6">
          Acesso exclusivo para profissionais e gestores
        </p>
      </div>
    </div>
  )
}
