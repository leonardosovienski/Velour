import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { ForgotPassword, ResetPassword } from './pages/PasswordRecovery'
import { Billing } from './pages/Billing'
import { Dashboard } from './pages/Dashboard'
import { Clients } from './pages/Clients'
import { ClientProfile } from './pages/ClientProfile'
import { Appointments } from './pages/Appointments'
import { Professionals } from './pages/Professionals'
import { Services } from './pages/Services'
import { Inventory } from './pages/Inventory'
import { Loyalty } from './pages/Loyalty'
import { Referrals } from './pages/Referrals'
import { Reports } from './pages/Reports'
import { Users } from './pages/Users'
import { Spinner } from './components/Spinner'

function SubscriptionRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    function subscriptionRequired() { navigate('/billing', { replace: true }) }
    window.addEventListener('velour:subscription-required', subscriptionRequired)
    return () => window.removeEventListener('velour:subscription-required', subscriptionRequired)
  }, [navigate])
  return null
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div className="min-h-screen bg-bg flex items-center justify-center">
      <Spinner size={40} />
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicRoute({ children, redirectTo = '/' }: { children: React.ReactNode; redirectTo?: string }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to={redirectTo} replace />
  return <>{children}</>
}

function StaffRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  return user?.role === 'professional' ? <Navigate to="/" replace /> : <>{children}</>
}

function SessionExpiredNotice() {
  const [expired, setExpired] = useState(false)
  const { user } = useAuth()
  useEffect(() => {
    function onExpired() { setExpired(true) }
    window.addEventListener('velour:session-expired', onExpired)
    return () => window.removeEventListener('velour:session-expired', onExpired)
  }, [])
  return expired && !user ? <div role="status" className="fixed bottom-4 left-4 right-4 z-50 bg-surface text-cream border border-gold/30 rounded-lg p-3 text-center text-sm">Sua sessão terminou. Entre novamente para continuar.</div> : null
}

function AppRoutes() {
  return (
    <><SubscriptionRedirect /><SessionExpiredNotice /><Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/signup" element={<PublicRoute redirectTo="/billing?welcome=1"><Signup /></PublicRoute>} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/billing" element={<ProtectedRoute><Billing /></ProtectedRoute>} />

      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/clients" element={<ProtectedRoute><Clients /></ProtectedRoute>} />
      <Route path="/clients/:id" element={<ProtectedRoute><ClientProfile /></ProtectedRoute>} />
      <Route path="/appointments" element={<ProtectedRoute><Appointments /></ProtectedRoute>} />
      <Route path="/professionals" element={<ProtectedRoute><Professionals /></ProtectedRoute>} />
      <Route path="/services" element={<ProtectedRoute><Services /></ProtectedRoute>} />
      <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
      <Route path="/loyalty" element={<ProtectedRoute><Loyalty /></ProtectedRoute>} />
      <Route path="/referrals" element={<ProtectedRoute><Referrals /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
      <Route path="/users" element={<ProtectedRoute><StaffRoute><Users /></StaffRoute></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes></>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
