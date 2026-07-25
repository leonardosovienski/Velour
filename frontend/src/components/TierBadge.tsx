import type { LoyaltyTier } from '../api/types'

const config: Record<LoyaltyTier, { label: string; className: string }> = {
  bronze:   { label: 'Bronze',   className: 'bg-amber-900/40 text-amber-400 border-amber-800/50' },
  silver:   { label: 'Silver',   className: 'bg-slate-700/40 text-slate-300 border-slate-600/50' },
  gold:     { label: 'Gold',     className: 'bg-yellow-900/40 text-gold border-gold-dim/50' },
  platinum: { label: 'Platinum', className: 'bg-violet-900/40 text-violet-300 border-violet-700/50' },
}

export function TierBadge({ tier, size = 'sm' }: { tier: LoyaltyTier; size?: 'xs' | 'sm' }) {
  const { label, className } = config[tier]
  return (
    <span className={`inline-flex items-center border rounded-full font-mono font-medium uppercase tracking-widest ${className} ${size === 'xs' ? 'text-[9px] px-2 py-0.5' : 'text-[10px] px-2.5 py-1'}`}>
      {label}
    </span>
  )
}
