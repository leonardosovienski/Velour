import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Search, Plus, ChevronRight, Phone, Mail } from 'lucide-react'
import { clientsApi } from '../api/client'
import type { ClientResponse, LoyaltyTier, ClientCreate, Gender, ChatPreference } from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { TierBadge } from '../components/TierBadge'
import { Modal } from '../components/Modal'
import { PageSpinner, Spinner } from '../components/Spinner'

const tiers: { value: string; label: string }[] = [
  { value: '', label: 'Todos os tiers' },
  { value: 'bronze', label: 'Bronze' },
  { value: 'silver', label: 'Silver' },
  { value: 'gold', label: 'Gold' },
  { value: 'platinum', label: 'Platinum' },
]

export function Clients() {
  const [clients, setClients] = useState<ClientResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [tier, setTier] = useState('')
  const [creating, setCreating] = useState(false)

  async function load() {
    setLoading(true)
    const data = await clientsApi.list({ tier: tier || undefined, limit: 100 })
    setClients(data)
    setLoading(false)
  }

  useEffect(() => { load() }, [tier])

  const filtered = clients.filter(c =>
    !search || c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.code.toLowerCase().includes(search.toLowerCase()) ||
    c.phone.includes(search)
  )

  return (
    <Layout>
      <PageHeader
        title="Clientes"
        subtitle={`${clients.length} clientes ativos`}
        action={
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors"
          >
            <Plus size={16} /> Novo Cliente
          </button>
        }
      />

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por nome, código ou telefone…"
            className="pl-9"
          />
        </div>
        <select value={tier} onChange={e => setTier(e.target.value)} className="w-44">
          {tiers.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      {loading ? <PageSpinner /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(client => (
            <Link key={client.id} to={`/clients/${client.id}`} className="block">
              <Card className="hover:border-gold/30 transition-colors cursor-pointer group">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
                    <span className="font-display text-base text-gold font-semibold">
                      {client.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-cream font-medium truncate group-hover:text-gold transition-colors">
                          {client.name}
                        </div>
                        <div className="text-muted text-xs font-mono">{client.code}</div>
                      </div>
                      <ChevronRight size={14} className="text-muted group-hover:text-gold transition-colors flex-shrink-0 mt-0.5" />
                    </div>

                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                      <TierBadge tier={client.loyalty_tier as LoyaltyTier} size="xs" />
                      <span className="text-muted text-xs font-mono">{client.loyalty_points.toLocaleString('pt-BR')} pts</span>
                    </div>

                    <div className="mt-2 space-y-1">
                      {client.phone && (
                        <div className="flex items-center gap-1.5 text-muted text-xs">
                          <Phone size={11} /> {client.phone}
                        </div>
                      )}
                      {client.email && (
                        <div className="flex items-center gap-1.5 text-muted text-xs truncate">
                          <Mail size={11} /> {client.email}
                        </div>
                      )}
                    </div>

                    <div className="mt-3 flex justify-between text-xs">
                      <span className="text-muted">{client.total_visits} visitas</span>
                      <span className="text-muted font-mono">
                        R${client.total_spent.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))}

          {!filtered.length && (
            <div className="col-span-3 text-center py-16 text-muted">
              Nenhum cliente encontrado.
            </div>
          )}
        </div>
      )}

      <CreateClientModal
        open={creating}
        onClose={() => setCreating(false)}
        onSuccess={() => { setCreating(false); load() }}
      />
    </Layout>
  )
}

function CreateClientModal({ open, onClose, onSuccess }: { open: boolean; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState<ClientCreate>({
    name: '', phone: '', gender: 'F', chat_preference: 'neutral',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function set(field: keyof ClientCreate, value: string) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await clientsApi.create(form)
      onSuccess()
      setForm({ name: '', phone: '', gender: 'F', chat_preference: 'neutral' })
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Erro ao criar cliente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title="Novo Cliente" open={open} onClose={onClose} width="max-w-xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="field-label">Nome completo *</label>
            <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="Maria da Silva" required />
          </div>
          <div>
            <label className="field-label">Telefone *</label>
            <input value={form.phone} onChange={e => set('phone', e.target.value)} placeholder="(11) 99999-9999" required />
          </div>
          <div>
            <label className="field-label">Email</label>
            <input type="email" value={form.email ?? ''} onChange={e => set('email', e.target.value)} placeholder="opcional" />
          </div>
          <div>
            <label className="field-label">Gênero *</label>
            <select value={form.gender} onChange={e => set('gender', e.target.value as Gender)}>
              <option value="F">Feminino</option>
              <option value="M">Masculino</option>
              <option value="other">Outro</option>
            </select>
          </div>
          <div>
            <label className="field-label">Data de nascimento</label>
            <input type="date" value={form.birthdate ?? ''} onChange={e => set('birthdate', e.target.value)} />
          </div>
          <div>
            <label className="field-label">Bebida preferida</label>
            <input value={form.preferred_drink ?? ''} onChange={e => set('preferred_drink', e.target.value)} placeholder="ex: Café sem açúcar" />
          </div>
          <div>
            <label className="field-label">Preferência musical</label>
            <input value={form.music_preference ?? ''} onChange={e => set('music_preference', e.target.value)} placeholder="ex: MPB, Lo-fi" />
          </div>
          <div>
            <label className="field-label">Temperatura</label>
            <input value={form.temperature_preference ?? ''} onChange={e => set('temperature_preference', e.target.value)} placeholder="ex: Ambiente frio" />
          </div>
          <div>
            <label className="field-label">Perfil de conversa</label>
            <select value={form.chat_preference} onChange={e => set('chat_preference', e.target.value as ChatPreference)}>
              <option value="quiet">Discreto</option>
              <option value="neutral">Neutro</option>
              <option value="chatty">Conversador</option>
            </select>
          </div>
          <div className="col-span-2">
            <label className="field-label">Alergias / Restrições</label>
            <input value={form.allergies ?? ''} onChange={e => set('allergies', e.target.value)} placeholder="ex: Alergia a amônia" />
          </div>
          <div className="col-span-2">
            <label className="field-label">Observações</label>
            <textarea value={form.notes ?? ''} onChange={e => set('notes', e.target.value)} rows={2} placeholder="Notas internas sobre a cliente…" />
          </div>
          <div className="col-span-2">
            <label className="field-label">Código de indicação usado</label>
            <input value={form.referral_code_used ?? ''} onChange={e => set('referral_code_used', e.target.value)} placeholder="Código de quem indicou (opcional)" />
          </div>
        </div>

        {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm transition-colors disabled:opacity-60">
            {loading ? <Spinner size={16} /> : 'Criar Cliente'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
