import { lazy, Suspense, useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
const Login = lazy(() => import('./pages/Login').then(module => ({ default: module.Login })))
const Signup = lazy(() => import('./pages/Signup').then(module => ({ default: module.Signup })))
const ForgotPassword = lazy(() => import('./pages/PasswordRecovery').then(module => ({ default: module.ForgotPassword })))
const ResetPassword = lazy(() => import('./pages/PasswordRecovery').then(module => ({ default: module.ResetPassword })))
const Finance = lazy(() => import('./pages/Finance').then(module => ({ default: module.Finance })))
const PlatformFiscal = lazy(() => import('./pages/Finance').then(module => ({ default: module.PlatformFiscal })))
const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })))
const Clients = lazy(() => import('./pages/Clients').then(module => ({ default: module.Clients })))
const ClientProfile = lazy(() => import('./pages/ClientProfile').then(module => ({ default: module.ClientProfile })))
const Appointments = lazy(() => import('./pages/Appointments').then(module => ({ default: module.Appointments })))
const Professionals = lazy(() => import('./pages/Professionals').then(module => ({ default: module.Professionals })))
const Services = lazy(() => import('./pages/Services').then(module => ({ default: module.Services })))
const Inventory = lazy(() => import('./pages/Inventory').then(module => ({ default: module.Inventory })))
const Loyalty = lazy(() => import('./pages/Loyalty').then(module => ({ default: module.Loyalty })))
const Referrals = lazy(() => import('./pages/Referrals').then(module => ({ default: module.Referrals })))
const Reports = lazy(() => import('./pages/Reports').then(module => ({ default: module.Reports })))
const Users = lazy(() => import('./pages/Users').then(module => ({ default: module.Users })))
import { Spinner } from './components/Spinner'
import { ErrorBoundary } from './components/ErrorBoundary'

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
  const location = useLocation()
  return (
    <><SubscriptionRedirect /><SessionExpiredNotice /><ErrorBoundary key={location.pathname}><Suspense fallback={<div role="status" className="min-h-screen bg-bg flex items-center justify-center text-muted"><Spinner size={32} /><span className="ml-3">Abrindo página…</span></div>}><Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/signup" element={<PublicRoute redirectTo="/billing?welcome=1"><Signup /></PublicRoute>} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/billing" element={<ProtectedRoute><Finance section="subscription" /></ProtectedRoute>} />
      <Route path="/finance" element={<ProtectedRoute><Finance /></ProtectedRoute>} />
      <Route path="/finance/:section" element={<ProtectedRoute><Finance /></ProtectedRoute>} />
      <Route path="/platform/fiscal" element={<ProtectedRoute><PlatformFiscal /></ProtectedRoute>} />
      <Route path="/fiscal" element={<ProtectedRoute><Navigate to="/finance/documents" replace /></ProtectedRoute>} />

      <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/clients" element={<ProtectedRoute><Clients /></ProtectedRoute>} />
      <Route path="/clients/:id" element={<ProtectedRoute><ClientProfile /></ProtectedRoute>} />
      <Route path="/appointments" element={<ProtectedRoute><Appointments /></ProtectedRoute>} />
      <Route path="/professionals" element={<ProtectedRoute><Professionals /></ProtectedRoute>} />
      <Route path="/services" element={<ProtectedRoute><Services /></ProtectedRoute>} />
      <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
      <Route path="/loyalty" element={<ProtectedRoute><Loyalty /></ProtectedRoute>} />
      <Route path="/referrals" element={<ProtectedRoute><Referrals /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><StaffRoute><Reports /></StaffRoute></ProtectedRoute>} />
      <Route path="/users" element={<ProtectedRoute><StaffRoute><Users /></StaffRoute></ProtectedRoute>} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes></Suspense></ErrorBoundary></>
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
