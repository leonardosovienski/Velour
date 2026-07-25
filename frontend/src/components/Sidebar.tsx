import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Calendar, Scissors,
  Star, Share2, BarChart2, LogOut, UserCog, ChevronRight, X, Package,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/',              icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/clients',       icon: Users,           label: 'Clientes' },
  { to: '/appointments',  icon: Calendar,        label: 'Agendamentos' },
  { to: '/professionals', icon: Scissors,        label: 'Profissionais' },
  { to: '/services',      icon: Scissors,        label: 'Serviços' },
  { to: '/inventory',     icon: Package,         label: 'Estoque' },
  { to: '/loyalty',       icon: Star,            label: 'Fidelidade' },
  { to: '/referrals',     icon: Share2,          label: 'Indicações' },
  { to: '/reports',       icon: BarChart2,       label: 'Relatórios' },
]

const adminItems = [
  { to: '/users', icon: UserCog, label: 'Usuários' },
]

export function Sidebar({ onClose }: { onClose?: () => void }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-56 flex-shrink-0 bg-surface border-r border-border flex flex-col h-full">
      {/* Logo */}
      <div className="px-6 py-7 border-b border-border flex items-start justify-between">
        <div>
          <div className="font-display text-2xl font-semibold text-gold tracking-wide">VELOUR</div>
          <div className="text-muted text-xs mt-0.5 tracking-widest uppercase">Gestão Premium</div>
        </div>
        {onClose && (
          <button onClick={onClose} className="md:hidden text-muted hover:text-cream p-1 mt-1">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-0.5 px-3">
          {navItems.map(({ to, icon: Icon, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors group ${
                    isActive
                      ? 'bg-gold/10 text-gold border border-gold/20'
                      : 'text-muted hover:text-cream hover:bg-white/5'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon size={16} className={isActive ? 'text-gold' : 'text-current'} />
                    <span className="flex-1">{label}</span>
                    {isActive && <ChevronRight size={12} className="text-gold/60" />}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        {(user?.role === 'admin' || user?.role === 'manager') && (
          <>
            <div className="px-6 mt-6 mb-2">
              <span className="text-[10px] text-muted uppercase tracking-widest">Administração</span>
            </div>
            <ul className="space-y-0.5 px-3">
              {adminItems.map(({ to, icon: Icon, label }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                        isActive
                          ? 'bg-gold/10 text-gold border border-gold/20'
                          : 'text-muted hover:text-cream hover:bg-white/5'
                      }`
                    }
                  >
                    <Icon size={16} />
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </>
        )}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-gold/10 border border-gold/20 flex items-center justify-center flex-shrink-0">
            <span className="font-display text-sm text-gold font-semibold">
              {user?.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="overflow-hidden">
            <div className="text-cream text-sm font-medium truncate">{user?.name}</div>
            <div className="text-muted text-[10px] capitalize">{user?.role}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full text-muted hover:text-danger text-sm px-2 py-1.5 rounded transition-colors hover:bg-danger/10"
        >
          <LogOut size={14} />
          Sair
        </button>
      </div>
    </aside>
  )
}
