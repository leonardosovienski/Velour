import { useEffect, useState, type FormEvent } from 'react'
import { format } from 'date-fns'
import {
  Plus, Package, AlertTriangle, CalendarClock, Pencil, PlusCircle, History, ToggleLeft, ToggleRight,
} from 'lucide-react'
import { productsApi } from '../api/client'
import type {
  ProductResponse, ProductCreate, ProductUpdate, ProductUnit,
  StockEntry, StockMovementType, StockMovementResponse,
} from '../api/types'
import { Layout, PageHeader } from '../components/Layout'
import { Modal } from '../components/Modal'
import { PageSpinner, Spinner } from '../components/Spinner'

const UNIT_LABEL: Record<ProductUnit, string> = { ml: 'ml', g: 'g', unit: 'un' }
const MOVE_LABEL: Record<StockMovementType, string> = {
  purchase: 'Entrada', consumption: 'Consumo', loss: 'Perda', adjustment: 'Ajuste',
}

function isExpiringSoon(date?: string): boolean {
  if (!date) return false
  const days = Math.ceil((new Date(date).getTime() - Date.now()) / 86_400_000)
  return days <= 30
}

function extractErrorDetail(err: unknown): string | undefined {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const anyErr = err as any
    return anyErr.response?.data?.detail
  }
  return undefined
}

export function Inventory() {
  const [products, setProducts] = useState<ProductResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [lowOnly, setLowOnly] = useState(false)
  const [editing, setEditing] = useState<ProductResponse | null>(null)
  const [creating, setCreating] = useState(false)
  const [stockFor, setStockFor] = useState<ProductResponse | null>(null)
  const [movementsFor, setMovementsFor] = useState<ProductResponse | null>(null)

  async function load() {
    setLoading(true)
    setProducts(await productsApi.list({ low_stock: lowOnly || undefined }))
    setLoading(false)
  }

  useEffect(() => { load() }, [lowOnly])

  async function toggleActive(p: ProductResponse) {
    await productsApi.update(p.id, { is_active: !p.is_active })
    load()
  }

  const lowCount = products.filter(p => p.stock_qty <= p.min_stock).length

  return (
    <Layout>
      <PageHeader
        title="Estoque"
        subtitle={`${products.length} insumos${lowCount ? ` · ${lowCount} abaixo do mínimo` : ''}`}
        action={
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-4 py-2.5 rounded-lg text-sm transition-colors"
          >
            <Plus size={16} /> Novo Insumo
          </button>
        }
      />

      <label className="flex items-center gap-2 mb-6 text-sm text-muted cursor-pointer w-fit">
        <input type="checkbox" checked={lowOnly} onChange={e => setLowOnly(e.target.checked)} className="accent-gold" />
        Mostrar apenas abaixo do mínimo
      </label>

      {loading ? <PageSpinner /> : !products.length ? (
        <div className="text-center py-16 text-muted">
          <Package size={28} className="mx-auto mb-3 opacity-50" />
          Nenhum insumo cadastrado.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-muted text-xs uppercase tracking-wider">
                <th className="text-left pb-3 pr-4">Insumo</th>
                <th className="text-right pb-3 pr-4">Saldo</th>
                <th className="text-right pb-3 pr-4">Mínimo</th>
                <th className="text-left pb-3 pr-4">Validade</th>
                <th className="text-right pb-3 pr-4">Custo/un</th>
                <th className="pb-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {products.map(p => {
                const low = p.stock_qty <= p.min_stock
                const exp = isExpiringSoon(p.expiry_date)
                return (
                  <tr key={p.id} className={`hover:bg-white/2 ${!p.is_active ? 'opacity-40' : ''}`}>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="text-cream font-medium">{p.name}</span>
                        {low && <AlertTriangle size={13} className="text-danger" />}
                      </div>
                    </td>
                    <td className={`py-3 pr-4 text-right font-mono ${low ? 'text-danger' : 'text-cream'}`}>
                      {p.stock_qty.toLocaleString('pt-BR')} {UNIT_LABEL[p.unit]}
                    </td>
                    <td className="py-3 pr-4 text-right font-mono text-muted">
                      {p.min_stock.toLocaleString('pt-BR')} {UNIT_LABEL[p.unit]}
                    </td>
                    <td className="py-3 pr-4">
                      {p.expiry_date ? (
                        <span className={`flex items-center gap-1.5 text-xs ${exp ? 'text-amber-400' : 'text-muted'}`}>
                          {exp && <CalendarClock size={12} />}
                          {format(new Date(p.expiry_date), 'dd/MM/yyyy')}
                        </span>
                      ) : <span className="text-muted text-xs">—</span>}
                    </td>
                    <td className="py-3 pr-4 text-right font-mono text-muted">
                      R${p.cost_per_unit.toFixed(2)}
                    </td>
                    <td className="py-3">
                      <div className="flex items-center justify-end gap-1.5">
                        <button onClick={() => setStockFor(p)} title="Movimentar estoque" className="text-muted hover:text-success p-1.5 transition-colors">
                          <PlusCircle size={14} />
                        </button>
                        <button onClick={() => setMovementsFor(p)} title="Histórico" className="text-muted hover:text-gold p-1.5 transition-colors">
                          <History size={14} />
                        </button>
                        <button onClick={() => setEditing(p)} title="Editar" className="text-muted hover:text-gold p-1.5 transition-colors">
                          <Pencil size={13} />
                        </button>
                        <button onClick={() => toggleActive(p)} title={p.is_active ? 'Desativar' : 'Ativar'}
                          className={`p-1 transition-colors ${p.is_active ? 'text-success hover:text-danger' : 'text-muted hover:text-success'}`}>
                          {p.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <ProductModal
        key={editing?.id ?? (creating ? 'creating' : 'product-none')}
        open={creating || !!editing}
        product={editing}
        onClose={() => { setCreating(false); setEditing(null) }}
        onSuccess={() => { setCreating(false); setEditing(null); load() }}
      />
      <StockModal
        key={stockFor?.id ?? 'stock-null'}
        product={stockFor}
        onClose={() => setStockFor(null)}
        onSuccess={() => { setStockFor(null); load() }}
      />
      <MovementsModal
        key={movementsFor?.id ?? 'movements-null'}
        product={movementsFor}
        onClose={() => setMovementsFor(null)}
      />
    </Layout>
  )
}

function ProductModal({ open, product, onClose, onSuccess }: {
  open: boolean; product: ProductResponse | null; onClose: () => void; onSuccess: () => void
}) {
  const blank: ProductCreate = { name: '', unit: 'ml', stock_qty: 0, min_stock: 0, cost_per_unit: 0 }
  const [form, setForm] = useState<ProductCreate>(() => product ? {
    name: product.name, unit: product.unit, stock_qty: product.stock_qty,
    min_stock: product.min_stock, expiry_date: product.expiry_date, cost_per_unit: product.cost_per_unit,
  } : blank)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function set<K extends keyof ProductCreate>(field: K, value: ProductCreate[K]) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (product) {
        const body: ProductUpdate = {
          name: form.name, unit: form.unit, min_stock: form.min_stock,
          expiry_date: form.expiry_date || undefined, cost_per_unit: form.cost_per_unit,
        }
        await productsApi.update(product.id, body)
      } else {
        await productsApi.create(form)
      }
      onSuccess()
    } catch (err: unknown) {
      const detail = extractErrorDetail(err)
      setError(detail ?? 'Erro ao salvar insumo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal title={product ? 'Editar Insumo' : 'Novo Insumo'} open={open} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="field-label">Nome *</label>
          <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="ex: Oxidante 20 vol" required />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="field-label">Unidade *</label>
            <select value={form.unit} onChange={e => set('unit', e.target.value as ProductUnit)}>
              <option value="ml">Mililitros (ml)</option>
              <option value="g">Gramas (g)</option>
              <option value="unit">Unidades</option>
            </select>
          </div>
          <div>
            <label className="field-label">Custo por unidade (R$)</label>
            <input type="number" step="0.01" min="0" value={form.cost_per_unit ?? 0}
              onChange={e => set('cost_per_unit', parseFloat(e.target.value) || 0)} />
          </div>
          {!product && (
            <div>
              <label className="field-label">Saldo inicial</label>
              <input type="number" step="0.01" min="0" value={form.stock_qty ?? 0}
                onChange={e => set('stock_qty', parseFloat(e.target.value) || 0)} />
            </div>
          )}
          <div>
            <label className="field-label">Estoque mínimo</label>
            <input type="number" step="0.01" min="0" value={form.min_stock ?? 0}
              onChange={e => set('min_stock', parseFloat(e.target.value) || 0)} />
          </div>
          <div className={product ? 'col-span-2' : ''}>
            <label className="field-label">Validade</label>
            <input type="date" value={form.expiry_date ?? ''} onChange={e => set('expiry_date', e.target.value)} />
          </div>
        </div>

        {!product && (
          <p className="text-muted text-xs">O saldo inicial gera uma entrada no histórico. Depois, o saldo só muda por movimentações.</p>
        )}
        {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
          <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
            {loading ? <Spinner size={16} /> : (product ? 'Salvar' : 'Criar Insumo')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function StockModal({ product, onClose, onSuccess }: {
  product: ProductResponse | null; onClose: () => void; onSuccess: () => void
}) {
  const [form, setForm] = useState<StockEntry>(() => ({ qty: 0, type: 'purchase' }))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!product) return
    setError('')
    setLoading(true)
    try {
      await productsApi.moveStock(product.id, form)
      onSuccess()
    } catch (err: unknown) {
      const detail = extractErrorDetail(err)
      setError(detail ?? 'Erro ao movimentar estoque.')
    } finally {
      setLoading(false)
    }
  }

  const sign = form.type === 'loss' ? -1 : 1
  const preview = product ? product.stock_qty + sign * (form.qty || 0) : 0

  return (
    <Modal title="Movimentar Estoque" open={!!product} onClose={onClose} width="max-w-sm">
      {product && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-bg rounded-lg p-3 border border-border text-sm">
            <div className="text-cream font-medium">{product.name}</div>
            <div className="text-muted text-xs">Saldo atual: {product.stock_qty.toLocaleString('pt-BR')} {UNIT_LABEL[product.unit]}</div>
          </div>
          <div>
            <label className="field-label">Tipo *</label>
            <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value as StockMovementType }))}>
              <option value="purchase">Entrada (compra)</option>
              <option value="adjustment">Ajuste (+)</option>
              <option value="loss">Perda / descarte (−)</option>
            </select>
          </div>
          <div>
            <label className="field-label">Quantidade ({UNIT_LABEL[product.unit]}) *</label>
            <input type="number" step="0.01" min="0.01" value={form.qty || ''}
              onChange={e => setForm(f => ({ ...f, qty: parseFloat(e.target.value) || 0 }))} required />
            <p className="text-muted text-xs mt-1">Novo saldo: <span className="font-mono text-cream">{preview.toLocaleString('pt-BR')} {UNIT_LABEL[product.unit]}</span></p>
          </div>
          <div>
            <label className="field-label">Descrição</label>
            <input value={form.description ?? ''} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="opcional" />
          </div>

          {error && <div className="text-red-400 text-sm bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">{error}</div>}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-muted hover:text-cream transition-colors">Cancelar</button>
            <button type="submit" disabled={loading} className="flex items-center gap-2 bg-gold hover:bg-gold/90 text-bg font-semibold px-5 py-2 rounded-lg text-sm disabled:opacity-60">
              {loading ? <Spinner size={16} /> : 'Registrar'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  )
}

function MovementsModal({ product, onClose }: { product: ProductResponse | null; onClose: () => void }) {
  const [movements, setMovements] = useState<StockMovementResponse[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!product) return
    setLoading(true)
    productsApi.movements(product.id).then(setMovements).finally(() => setLoading(false))
  }, [product])

  return (
    <Modal title={`Histórico — ${product?.name ?? ''}`} open={!!product} onClose={onClose}>
      {loading ? <div className="py-8 flex justify-center"><Spinner size={24} /></div> : !movements.length ? (
        <div className="text-center py-8 text-muted text-sm">Nenhuma movimentação registrada.</div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {movements.map(m => (
            <div key={m.id} className="flex items-center justify-between bg-bg border border-border rounded-lg px-3 py-2 text-sm">
              <div>
                <div className="text-cream">{MOVE_LABEL[m.type]}</div>
                <div className="text-muted text-xs">
                  {format(new Date(m.created_at), 'dd/MM/yyyy HH:mm')}
                  {m.appointment_id ? ` · atend. #${m.appointment_id}` : ''}
                </div>
              </div>
              <div className="text-right">
                <div className={`font-mono ${m.qty < 0 ? 'text-danger' : 'text-success'}`}>
                  {m.qty > 0 ? '+' : ''}{m.qty.toLocaleString('pt-BR')}
                </div>
                <div className="text-muted text-xs font-mono">→ {m.qty_after.toLocaleString('pt-BR')}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}
