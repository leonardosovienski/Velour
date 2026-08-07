import { useEffect, useState, type FormEvent } from 'react'
import { Plus, ToggleRight, ToggleLeft, Pencil, ShieldCheck, Shield, User } from 'lucide-react'
import { usersApi, getErrorDetail } from '../api/client'
import type { UserResponse, UserRole } from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { Modal } from '../components/Modal'
import { PageSpinner, Spinner } from '../components/Spinner'

const roleLabel: Record<UserRole, string> = {
  admin: 'Administrador',
  manager: 'Gerente',
  professional: 'Profissional',
}

const roleIcon: Record<UserRole, typeof ShieldCheck> = {
  admin: ShieldCheck,
  manager: Shield,
  professional: User,
}

const roleColor: Record<UserRole, string> = {
  admin: 'text-gold',
  manager: 'text-blue-400',
  professional: 'text-muted',
}

export function Users() {
  const [users, setUsers] = useState<UserResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [editing, setEditing] = useState<UserResponse | null>(null)

  async function load() {
    setLoading(true)
    const data = await usersApi.list()
    setUsers(data)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  async function handleToggleActive(u: UserResponse) {
    await usersApi.update(u.id, { is_active: !u.is_active })
    load()
  }

  return (
    <Layout>
      <PageHeader
        title="Usuários"
        subtitle={`${users.length} usuários cadastrados`}
        action={
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors"
          >
            <Plus size={16} /> Novo Usuário
          </button>
        }
      />

      {loading ? <PageSpinner /> : (
        <Card className="p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted text-xs uppercase tracking-wider">
                <th className="text-left px-5 py-3">Usuário</th>
                <th className="text-left px-5 py-3">Email</th>
                <th className="text-left px-5 py-3">Perfil</th>
                <th className="text-left px-5 py-3">Status</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map(u => {
                const RoleIcon = roleIcon[u.role]
                return (
                  <tr key={u.id} className={`hover:bg-white/2 transition-colors ${!u.is_active ? 'opacity-50' : ''}`}>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
                          <span className="font-display text-sm text-gold font-semibold">
                            {u.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="text-cream font-medium">{u.name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-muted">{u.email}</td>
                    <td className="px-5 py-4">
                      <span className={`flex items-center gap-1.5 text-xs font-medium ${roleColor[u.role]}`}>
                        <RoleIcon size={13} /> {roleLabel[u.role]}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded-full border ${u.is_active ? 'text-green-400 border-success/40 bg-success/10' : 'text-muted border-border'}`}>
                        {u.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => setEditing(u)}
                          title="Editar"
                          className="text-muted hover:text-gold p-1.5 transition-colors"
                        >
                          <Pencil size={13} />
                        </button>
                        <button
                          onClick={() => handleToggleActive(u)}
                          title={u.is_active ? 'Desativar' : 'Ativar'}
                          className={`p-1.5 transition-colors ${u.is_active ? 'text-success hover:text-red-400' : 'text-muted hover:text-success'}`}
                        >
                          {u.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
              {!users.length && (
                <tr>
                  <td colSpan={5} className="text-center py-16 text-muted">Nenhum usuário encontrado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      <UserModal
        open={creating || !!editing}
        user={editing}
        onClose={() => { setCreating(false); setEditing(null) }}
        onSuccess={() => { setCreating(false); setEditing(null); load() }}
      />
    </Layout>
  )
}

function UserModal({ open, user, onClose, onSuccess }: {
  open: boolean
  user: UserResponse | null
  onClose: () => void
  onSuccess: () => void
}) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>('professional')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (user) {
      setName(user.name)
      setEmail(user.email)
      setRole(user.role)
      setPassword('')
    } else {
      setName(''); setEmail(''); setPassword(''); setRole('professional')
    }
    setError('')
  }, [user, open])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (user) {
        await usersApi.update(user.id, { name, role })
      } else {
        await usersApi.create({ name, email, password, role })
      }
      onSuccess()
    } catch (err) {
      setError(getErrorDetail(err) ?? 'Erro ao salvar usuário.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={user ? 'Editar Usuário' : 'Novo Usuário'} open={open} onClose={onClose} width="max-w-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="field-label">Nome completo *</label>
          <input value={name} onChange={e => setName(e.target.value)} required />
        </div>
        {!user && (
          <div>
            <label className="field-label">Email *</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
        )}
        {!user && (
          <div>
            <label className="field-label">Senha * (mínimo 6 caracteres)</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={6} required />
          </div>
        )}
        <div>
          <label className="field-label">Perfil *</label>
          <select value={role} onChange={e => setRole(e.target.value as UserRole)}>
            <option value="professional">Profissional</option>
            <option value="manager">Gerente</option>
            <option value="admin">Administrador</option>
          </select>
        </div>

        {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
            {loading ? <Spinner size={16} /> : (user ? 'Salvar' : 'Criar Usuário')}
          </button>
        </div>
      </form>
    </Modal>
  )
}
