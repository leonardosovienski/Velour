import axios from 'axios'
import type {
  LoginResponse, UserResponse, UserCreate, UserUpdate,
  ClientResponse, ClientBriefing, ClientCreate, ClientUpdate,
  ProfessionalResponse, ProfessionalStats, ProfessionalCreate, ProfessionalUpdate,
  ServiceCategoryResponse, ServiceResponse, ServiceCreate, ServiceUpdate,
  AppointmentDetail, AppointmentCreate, AppointmentComplete,
  LoyaltyTransactionResponse, LoyaltyOverview,
  ReferralResponse, ReferralRankingItem,
  DashboardToday, DashboardKPIs, WeeklyRevenueItem, DashboardAlerts, TodayAppointment,
  RevenueReport, ClientReport, LoyaltyMonthlyItem, ReferralMonthlyItem,
  ProductResponse, ProductCreate, ProductUpdate, StockEntry, StockMovementResponse,
  RecipeItem, ServiceRecipeResponse, ProfessionalDashboard,
} from './types'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const params = new URLSearchParams({ username: email, password })
    const { data } = await api.post<LoginResponse>('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },
  me: () => api.get('/auth/me').then(r => r.data),
}

// Users
export const usersApi = {
  list: () => api.get<UserResponse[]>('/users').then(r => r.data),
  create: (body: UserCreate) => api.post<UserResponse>('/users', body).then(r => r.data),
  update: (id: number, body: UserUpdate) =>
    api.patch<UserResponse>(`/users/${id}`, body).then(r => r.data),
}

// Clients
export const clientsApi = {
  list: (params?: { tier?: string; limit?: number; offset?: number }) =>
    api.get<ClientResponse[]>('/clients', { params }).then(r => r.data),
  get: (id: number) => api.get<ClientResponse>(`/clients/${id}`).then(r => r.data),
  briefing: (id: number) => api.get<ClientBriefing>(`/clients/${id}/briefing`).then(r => r.data),
  create: (body: ClientCreate) => api.post<ClientResponse>('/clients', body).then(r => r.data),
  update: (id: number, body: ClientUpdate) =>
    api.patch<ClientResponse>(`/clients/${id}`, body).then(r => r.data),
  deactivate: (id: number) => api.delete(`/clients/${id}`),
}

// Professionals
export const professionalsApi = {
  list: () => api.get<ProfessionalResponse[]>('/professionals').then(r => r.data),
  get: (id: number) => api.get<ProfessionalResponse>(`/professionals/${id}`).then(r => r.data),
  stats: (id: number) => api.get<ProfessionalStats>(`/professionals/${id}/stats`).then(r => r.data),
  dashboard: (id: number) =>
    api.get<ProfessionalDashboard>(`/professionals/${id}/dashboard`).then(r => r.data),
  create: (body: ProfessionalCreate) =>
    api.post<ProfessionalResponse>('/professionals', body).then(r => r.data),
  update: (id: number, body: ProfessionalUpdate) =>
    api.patch<ProfessionalResponse>(`/professionals/${id}`, body).then(r => r.data),
  deactivate: (id: number) => api.delete(`/professionals/${id}`),
}

// Services
export const serviceCategoriesApi = {
  list: () => api.get<ServiceCategoryResponse[]>('/service-categories').then(r => r.data),
  create: (body: { name: string; gender_target?: string; icon?: string }) =>
    api.post<ServiceCategoryResponse>('/service-categories', body).then(r => r.data),
  update: (id: number, body: { name?: string; gender_target?: string }) =>
    api.patch<ServiceCategoryResponse>(`/service-categories/${id}`, body).then(r => r.data),
  delete: (id: number) => api.delete(`/service-categories/${id}`),
}

export const servicesApi = {
  list: (params?: { category_id?: number; is_active?: boolean }) =>
    api.get<ServiceResponse[]>('/services', { params }).then(r => r.data),
  get: (id: number) => api.get<ServiceResponse>(`/services/${id}`).then(r => r.data),
  create: (body: ServiceCreate) => api.post<ServiceResponse>('/services', body).then(r => r.data),
  update: (id: number, body: ServiceUpdate) =>
    api.patch<ServiceResponse>(`/services/${id}`, body).then(r => r.data),
  deactivate: (id: number) => api.delete(`/services/${id}`),
}

// Products / estoque
export const productsApi = {
  list: (params?: { is_active?: boolean; low_stock?: boolean }) =>
    api.get<ProductResponse[]>('/products', { params }).then(r => r.data),
  get: (id: number) => api.get<ProductResponse>(`/products/${id}`).then(r => r.data),
  create: (body: ProductCreate) => api.post<ProductResponse>('/products', body).then(r => r.data),
  update: (id: number, body: ProductUpdate) =>
    api.patch<ProductResponse>(`/products/${id}`, body).then(r => r.data),
  deactivate: (id: number) => api.delete(`/products/${id}`),
  moveStock: (id: number, body: StockEntry) =>
    api.post<ProductResponse>(`/products/${id}/stock`, body).then(r => r.data),
  movements: (id: number) =>
    api.get<StockMovementResponse[]>(`/products/${id}/movements`).then(r => r.data),
}

// Ficha técnica (receita do serviço)
export const recipesApi = {
  get: (serviceId: number) =>
    api.get<ServiceRecipeResponse[]>(`/services/${serviceId}/recipe`).then(r => r.data),
  set: (serviceId: number, items: RecipeItem[]) =>
    api.put<ServiceRecipeResponse[]>(`/services/${serviceId}/recipe`, items).then(r => r.data),
}

// Appointments
export const appointmentsApi = {
  list: (params?: {
    date_from?: string; date_to?: string; status?: string;
    professional_id?: number; client_id?: number; limit?: number; offset?: number
  }) => api.get<AppointmentDetail[]>('/appointments', { params }).then(r => r.data),
  get: (id: number) => api.get<AppointmentDetail>(`/appointments/${id}`).then(r => r.data),
  create: (body: AppointmentCreate) =>
    api.post<AppointmentDetail>('/appointments', body).then(r => r.data),
  updateStatus: (id: number, status: string) =>
    api.patch(`/appointments/${id}/status`, { status }).then(r => r.data),
  complete: (id: number, body: AppointmentComplete) =>
    api.post(`/appointments/${id}/complete`, body).then(r => r.data),
  cancel: (id: number) => api.delete(`/appointments/${id}`),
  uploadPhotos: (id: number, photoBefore?: File, photoAfter?: File) => {
    const fd = new FormData()
    if (photoBefore) fd.append('photo_before', photoBefore)
    if (photoAfter) fd.append('photo_after', photoAfter)
    return api.post(`/appointments/${id}/photos`, fd).then(r => r.data)
  },
}

// Loyalty
export const loyaltyApi = {
  transactions: (params?: { client_id?: number; limit?: number }) =>
    api.get<LoyaltyTransactionResponse[]>('/loyalty/transactions', { params }).then(r => r.data),
  overview: () => api.get<LoyaltyOverview>('/loyalty/overview').then(r => r.data),
}

// Referrals
export const referralsApi = {
  list: (params?: { status?: string; limit?: number }) =>
    api.get<ReferralResponse[]>('/referrals', { params }).then(r => r.data),
  ranking: () => api.get<ReferralRankingItem[]>('/referrals/ranking').then(r => r.data),
}

// Dashboard
export const dashboardApi = {
  today: () => api.get<DashboardToday>('/dashboard/today').then(r => r.data),
  kpis: (period: 'day' | 'week' | 'month' = 'day') =>
    api.get<DashboardKPIs>('/dashboard/kpis', { params: { period } }).then(r => r.data),
  weeklyRevenue: () => api.get<WeeklyRevenueItem[]>('/dashboard/weekly-revenue').then(r => r.data),
  alerts: () => api.get<DashboardAlerts>('/dashboard/alerts').then(r => r.data),
  upcoming: (days = 2) =>
    api.get<TodayAppointment[]>('/dashboard/upcoming', { params: { days } }).then(r => r.data),
}

// Reports
export const reportsApi = {
  revenue: (params?: { period_start?: string; period_end?: string; professional_id?: number }) =>
    api.get<RevenueReport>('/reports/revenue', { params }).then(r => r.data),
  clients: (params?: { period_start?: string; period_end?: string }) =>
    api.get<ClientReport>('/reports/clients', { params }).then(r => r.data),
  loyaltyMonthly: (months = 6) =>
    api.get<LoyaltyMonthlyItem[]>('/reports/loyalty-monthly', { params: { months } }).then(r => r.data),
  referralsMonthly: (months = 6) =>
    api.get<ReferralMonthlyItem[]>('/reports/referrals-monthly', { params: { months } }).then(r => r.data),
}

export default api
