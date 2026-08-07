import { useEffect, useState, type FormEvent } from 'react'
import {
  Plus, Tag, Clock, DollarSign, Star, Pencil, FlaskConical, Trash2,
  Scissors, Palette, Sparkles, Gem, Zap, Flower2, Droplets, Crown,
  type LucideIcon,
} from 'lucide-react'
import { servicesApi, serviceCategoriesApi, productsApi, recipesApi, getErrorDetail } from '../api/client'
import type {
  ServiceResponse, ServiceCategoryResponse, ServiceCreate, ServiceUpdate,
  ProductResponse, RecipeItem,
} from '../api/types'
import { Layout, PageHeader, Card } from '../components/Layout'
import { Modal } from '../components/Modal'
import { PageSpinner, Spinner } from '../components/Spinner'

const ICON_MAP: Record<string, LucideIcon> = {
  scissors: Scissors,
  palette: Palette,
  sparkles: Sparkles,
  gem: Gem,
  zap: Zap,
  flower: Flower2,
  flower2: Flower2,
  droplets: Droplets,
  crown: Crown,
  razor: Scissors,
}

function CatIcon({ name }: { name?: string | null }) {
  const Icon = name ? ICON_MAP[name.toLowerCase()] : null
  if (Icon) return <Icon size={22} className="text-gold" />
  return <Scissors size={22} className="text-gold" />
}

export function Services() {
  const [tab, setTab] = useState<'services' | 'categories'>('services')
  const [services, setServices] = useState<ServiceResponse[]>([])
  const [categories, setCategories] = useState<ServiceCategoryResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [creatingService, setCreatingService] = useState(false)
  const [editingService, setEditingService] = useState<ServiceResponse | null>(null)
  const [recipeFor, setRecipeFor] = useState<ServiceResponse | null>(null)
  const [creatingCat, setCreatingCat] = useState(false)

  async function load() {
    setLoading(true)
    const [s, c] = await Promise.all([servicesApi.list(), serviceCategoriesApi.list()])
    setServices(s)
    setCategories(c)
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const categoryMap = Object.fromEntries(categories.map(c => [c.id, c]))

  return (
    <Layout>
      <PageHeader
        title="Serviços"
        subtitle="Gestão de serviços e categorias"
        action={
          <div className="flex gap-2">
            {tab === 'categories' && (
              <button onClick={() => setCreatingCat(true)} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors">
                <Plus size={16} /> Nova Categoria
              </button>
            )}
            {tab === 'services' && (
              <button onClick={() => setCreatingService(true)} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors">
                <Plus size={16} /> Novo Serviço
              </button>
            )}
          </div>
        }
      />

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-surface rounded-lg border border-border w-fit mb-6">
        {(['services', 'categories'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t ? 'bg-gold/10 text-gold border border-gold/20' : 'text-muted hover:text-cream'}`}
          >
            {t === 'services' ? 'Serviços' : 'Categorias'}
          </button>
        ))}
      </div>

      {loading ? <PageSpinner /> : tab === 'services' ? (
        <div className="space-y-2">
          {!services.length ? (
            <div className="text-center py-16 text-muted">Nenhum serviço cadastrado.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted text-xs uppercase tracking-wider">
                    <th className="text-left pb-3 pr-4">Serviço</th>
                    <th className="text-left pb-3 pr-4">Categoria</th>
                    <th className="text-left pb-3 pr-4"><Clock size={12} className="inline" /> Duração</th>
                    <th className="text-left pb-3 pr-4"><DollarSign size={12} className="inline" /> Preço</th>
                    <th className="text-left pb-3 pr-4"><Star size={12} className="inline" /> Pontos</th>
                    <th className="text-left pb-3">Status</th>
                    <th className="pb-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {services.map(svc => (
                    <tr key={svc.id} className="hover:bg-white/2">
                      <td className="py-3 pr-4">
                        <div className="text-cream font-medium">{svc.name}</div>
                        {svc.description && <div className="text-muted text-xs truncate max-w-xs">{svc.description}</div>}
                      </td>
                      <td className="py-3 pr-4">
                        <span className="flex items-center gap-1.5 text-muted text-xs">
                          <Tag size={11} /> {categoryMap[svc.category_id]?.name ?? `Cat. #${svc.category_id}`}
                        </span>
                      </td>
                      <td className="py-3 pr-4 font-mono text-muted">{svc.duration_minutes} min</td>
                      <td className="py-3 pr-4 font-mono text-cream">R${svc.price.toFixed(2)}</td>
                      <td className="py-3 pr-4 font-mono text-gold">{svc.points_reward}</td>
                      <td className="py-3 pr-4">
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${svc.is_active ? 'text-green-400 border-success/40 bg-success/10' : 'text-muted border-border bg-surface'}`}>
                          {svc.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="py-3">
                        <div className="flex items-center justify-end gap-1.5">
                          <button onClick={() => setRecipeFor(svc)} title="Ficha técnica" className="text-muted hover:text-gold p-1.5 transition-colors">
                            <FlaskConical size={14} />
                          </button>
                          <button onClick={() => setEditingService(svc)} title="Editar" className="text-muted hover:text-gold p-1.5 transition-colors">
                            <Pencil size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
          {categories.map(cat => (
            <Card key={cat.id}>
              <div className="mb-3"><CatIcon name={cat.icon} /></div>
              <div className="text-cream font-medium">{cat.name}</div>
              <div className="text-muted text-xs mt-1 capitalize">{cat.gender_target === 'all' ? 'Todos' : cat.gender_target}</div>
              <div className="text-muted text-xs mt-2">
                {services.filter(s => s.category_id === cat.id).length} serviços
              </div>
            </Card>
          ))}
          {!categories.length && (
            <div className="col-span-4 text-center py-16 text-muted">Nenhuma categoria.</div>
          )}
        </div>
      )}

      <ServiceModal
        open={creatingService || !!editingService}
        service={editingService}
        categories={categories}
        onClose={() => { setCreatingService(false); setEditingService(null) }}
        onSuccess={() => { setCreatingService(false); setEditingService(null); load() }}
      />

      <CategoryModal
        open={creatingCat}
        onClose={() => setCreatingCat(false)}
        onSuccess={() => { setCreatingCat(false); load() }}
      />

      <RecipeModal service={recipeFor} onClose={() => setRecipeFor(null)} />
    </Layout>
  )
}

function RecipeModal({ service, onClose }: { service: ServiceResponse | null; onClose: () => void }) {
  const [products, setProducts] = useState<ProductResponse[]>([])
  const [items, setItems] = useState<RecipeItem[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!service) return
    setError('')
    setLoading(true)
    Promise.all([productsApi.list(), recipesApi.get(service.id)])
      .then(([prods, recipe]) => {
        setProducts(prods)
        setItems(recipe.map(r => ({ product_id: r.product_id, qty_consumed: r.qty_consumed })))
      })
      .finally(() => setLoading(false))
  }, [service])

  const productMap = Object.fromEntries(products.map(p => [p.id, p]))
  const available = products.filter(p => p.is_active && !items.some(i => i.product_id === p.id))

  function addItem() {
    if (!available.length) return
    setItems(i => [...i, { product_id: available[0].id, qty_consumed: 0 }])
  }
  function updateItem(idx: number, patch: Partial<RecipeItem>) {
    setItems(i => i.map((it, k) => k === idx ? { ...it, ...patch } : it))
  }
  function removeItem(idx: number) {
    setItems(i => i.filter((_, k) => k !== idx))
  }

  async function save() {
    if (!service) return
    setError('')
    setSaving(true)
    try {
      await recipesApi.set(service.id, items.filter(i => i.qty_consumed > 0))
      onClose()
    } catch (err) {
      setError(getErrorDetail(err) ?? 'Erro ao salvar ficha técnica.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={`Ficha Técnica — ${service?.name ?? ''}`} open={!!service} onClose={onClose}>
      {loading ? (
        <div className="py-10 flex justify-center"><Spinner size={28} /></div>
      ) : (
        <div className="space-y-4">
          <p className="text-muted text-xs">
            Defina os insumos consumidos por execução. Ao concluir o atendimento, o estoque é baixado automaticamente (ajustável no checkout).
          </p>

          {!products.length ? (
            <div className="text-muted text-sm bg-bg border border-border rounded-lg p-3">
              Nenhum insumo cadastrado ainda. Cadastre em <span className="text-gold">Estoque</span> primeiro.
            </div>
          ) : !items.length ? (
            <div className="text-muted text-sm text-center py-4">Nenhum insumo na ficha técnica.</div>
          ) : (
            <div className="space-y-2">
              {items.map((item, idx) => {
                const prod = productMap[item.product_id]
                return (
                  <div key={idx} className="flex items-center gap-2">
                    <select value={item.product_id} onChange={e => updateItem(idx, { product_id: Number(e.target.value) })} className="flex-1">
                      {prod && <option value={prod.id}>{prod.name}</option>}
                      {available.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                    <input type="number" step="0.01" min="0" value={item.qty_consumed}
                      onChange={e => updateItem(idx, { qty_consumed: parseFloat(e.target.value) || 0 })}
                      className="w-24 text-right" />
                    <span className="text-muted text-xs w-6">{prod?.unit ?? ''}</span>
                    <button onClick={() => removeItem(idx)} className="text-muted hover:text-danger p-1.5 transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </div>
                )
              })}
            </div>
          )}

          {available.length > 0 && (
            <button onClick={addItem} className="flex items-center gap-1.5 text-sm text-gold hover:text-gold/80 transition-colors">
              <Plus size={14} /> Adicionar insumo
            </button>
          )}

          {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

          <div className="flex justify-end gap-3 pt-2 border-t border-border">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
            <button onClick={save} disabled={saving} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
              {saving ? <Spinner size={16} /> : 'Salvar Ficha'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}

function ServiceModal({ open, service, categories, onClose, onSuccess }: {
  open: boolean
  service: ServiceResponse | null
  categories: ServiceCategoryResponse[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [form, setForm] = useState<ServiceCreate>({ category_id: 0, name: '', duration_minutes: 30, price: 0, points_reward: 0 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (service) {
      setForm({ category_id: service.category_id, name: service.name, description: service.description, duration_minutes: service.duration_minutes, price: service.price, points_reward: service.points_reward })
    } else {
      setForm({ category_id: categories[0]?.id ?? 0, name: '', duration_minutes: 30, price: 0, points_reward: 0 })
    }
  }, [service, open])

  function set(field: keyof ServiceCreate, value: string | number) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (service) {
        await servicesApi.update(service.id, form as ServiceUpdate)
      } else {
        await servicesApi.create(form)
      }
      onSuccess()
    } catch (err) {
      setError(getErrorDetail(err) ?? 'Erro ao salvar serviço.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={service ? 'Editar Serviço' : 'Novo Serviço'} open={open} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="field-label">Nome *</label>
          <input value={form.name} onChange={e => set('name', e.target.value)} required />
        </div>
        <div>
          <label className="field-label">Categoria *</label>
          <select value={form.category_id} onChange={e => set('category_id', Number(e.target.value))} required>
            <option value={0}>Selecione</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div>
          <label className="field-label">Descrição</label>
          <input value={form.description ?? ''} onChange={e => set('description', e.target.value)} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="field-label">Duração (min) *</label>
            <input type="number" min="1" value={form.duration_minutes} onChange={e => set('duration_minutes', parseInt(e.target.value) || 0)} required />
          </div>
          <div>
            <label className="field-label">Preço (R$) *</label>
            <input type="number" step="0.01" min="0" value={form.price} onChange={e => set('price', parseFloat(e.target.value) || 0)} required />
          </div>
          <div>
            <label className="field-label">Pontos</label>
            <input type="number" min="0" value={form.points_reward ?? 0} onChange={e => set('points_reward', parseInt(e.target.value) || 0)} />
          </div>
        </div>

        {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
            {loading ? <Spinner size={16} /> : (service ? 'Salvar' : 'Criar')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function CategoryModal({ open, onClose, onSuccess }: { open: boolean; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState({ name: '', gender_target: 'all', icon: '' })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    await serviceCategoriesApi.create(form)
    setLoading(false)
    onSuccess()
    setForm({ name: '', gender_target: 'all', icon: '' })
  }

  return (
    <Modal title="Nova Categoria" open={open} onClose={onClose} width="max-w-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div><label className="field-label">Nome *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required /></div>
        <div>
          <label className="field-label">Público</label>
          <select value={form.gender_target} onChange={e => setForm(f => ({ ...f, gender_target: e.target.value }))}>
            <option value="all">Todos</option>
            <option value="F">Feminino</option>
            <option value="M">Masculino</option>
          </select>
        </div>
        <div><label className="field-label">Emoji / Ícone</label><input value={form.icon} onChange={e => setForm(f => ({ ...f, icon: e.target.value }))} placeholder="✂️" /></div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
            {loading ? <Spinner size={16} /> : 'Criar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
