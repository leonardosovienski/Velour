export type UserRole = 'admin' | 'manager' | 'professional'
export type Gender = 'M' | 'F' | 'other'
export type ChatPreference = 'chatty' | 'quiet' | 'neutral'
export type LoyaltyTier = 'bronze' | 'silver' | 'gold' | 'platinum'
export type AppointmentStatus = 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show'
export type LoyaltyTxType = 'earned_appointment' | 'earned_referral' | 'earned_birthday' | 'redeemed'
export type ReferralStatus = 'pending' | 'converted'

// Auth
export interface UserCreate {
  name: string
  email: string
  password: string
  role: UserRole
}

export interface UserUpdate {
  name?: string
  role?: UserRole
  is_active?: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  role: UserRole
  name: string
}

// User
export interface UserResponse {
  id: number
  name: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

// Client
export interface ClientResponse {
  id: number
  code: string
  name: string
  phone: string
  email?: string
  gender: Gender
  birthdate?: string
  first_visit: string
  photo_url?: string
  preferred_drink?: string
  music_preference?: string
  temperature_preference?: string
  chat_preference: ChatPreference
  allergies?: string
  notes?: string
  loyalty_points: number
  loyalty_tier: LoyaltyTier
  total_spent: number
  total_visits: number
  referral_code: string
  referred_by_id?: number
  is_active: boolean
  created_at: string
}

export interface ClientBriefing {
  id: number
  code: string
  name: string
  loyalty_tier: LoyaltyTier
  loyalty_points: number
  total_spent: number
  total_visits: number
  first_visit: string
  preferred_drink?: string
  music_preference?: string
  temperature_preference?: string
  chat_preference: ChatPreference
  allergies?: string
  notes?: string
  last_appointment?: {
    date: string
    professional_name: string
    service_name: string
    formula_used?: string
    notes?: string
  }
  spent_to_next_tier?: number
}

export interface ClientCreate {
  name: string
  phone: string
  email?: string
  gender: Gender
  birthdate?: string
  preferred_drink?: string
  music_preference?: string
  temperature_preference?: string
  chat_preference: ChatPreference
  allergies?: string
  notes?: string
  referral_code_used?: string
}

export type ClientUpdate = Partial<ClientCreate & { is_active: boolean }>

// Professional
export interface ProfessionalResponse {
  id: number
  name: string
  phone: string
  email?: string
  gender: Gender
  photo_url?: string
  specialty: string
  bio?: string
  commission_rate: number
  monthly_goal: number
  is_active: boolean
  created_at: string
}

export interface ProfessionalStats {
  professional_id: number
  name: string
  appointments_this_month: number
  revenue_this_month: number
  commission_this_month: number
  average_ticket: number
  top_service?: string
}

export interface ProfessionalCreate {
  name: string
  phone: string
  email?: string
  gender: Gender
  specialty: string
  bio?: string
  commission_rate: number
  monthly_goal?: number
}

export interface ProfessionalDashboard {
  professional_id: number
  name: string
  monthly_goal: {
    target: number
    revenue: number
    commission: number
    progress: number | null
    remaining: number | null
  }
  inactive_clients: {
    client_id: number
    name: string
    code: string
    tier: LoyaltyTier
    last_visit: string
    avg_cadence_days: number
    days_since_last: number
    overdue_by_days: number
  }[]
}

export type ProfessionalUpdate = Partial<ProfessionalCreate & { is_active: boolean }>

// Service
export interface ServiceCategoryResponse {
  id: number
  name: string
  gender_target: 'M' | 'F' | 'all'
  icon?: string
}

export interface ServiceResponse {
  id: number
  category_id: number
  category?: ServiceCategoryResponse
  name: string
  description?: string
  duration_minutes: number
  price: number
  points_reward: number
  is_active: boolean
  created_at: string
}

export interface ServiceCreate {
  category_id: number
  name: string
  description?: string
  duration_minutes: number
  price: number
  points_reward?: number
}

export type ServiceUpdate = Partial<ServiceCreate & { is_active: boolean }>

// Appointment
export interface AppointmentResponse {
  id: number
  client_id: number
  professional_id: number
  service_id: number
  scheduled_at: string
  ends_at: string
  status: AppointmentStatus
  occasion?: string
  notes?: string
  photo_before_url?: string
  photo_after_url?: string
  formula_used?: string
  points_awarded: number
  price_charged?: number
  discount_points_used: number
  tier_at_service?: LoyaltyTier
  tier_discount_amount: number
  created_at: string
}

export interface AppointmentDetail extends AppointmentResponse {
  client?: ClientResponse
  professional?: ProfessionalResponse
  service?: ServiceResponse
}

export interface AppointmentCreate {
  client_id: number
  professional_id: number
  service_id: number
  scheduled_at: string
  occasion?: string
  notes?: string
}

export interface RecipeOverride {
  product_id: number
  actual_qty: number
}

export interface AppointmentComplete {
  price_charged: number
  discount_points_used?: number
  photo_before_url?: string
  photo_after_url?: string
  formula_used?: string
  notes?: string
  recipe_overrides?: RecipeOverride[]
}

// Loyalty
export interface LoyaltyTransactionResponse {
  id: number
  client_id: number
  appointment_id?: number
  referral_id?: number
  type: LoyaltyTxType
  points: number
  description: string
  created_at: string
}

export interface LoyaltyOverview {
  total_points_in_circulation: number
  points_issued_this_month: number
  points_redeemed_this_month: number
  tier_distribution: { tier: LoyaltyTier; count: number }[]
  top_clients: { id: number; code: string; name: string; tier: LoyaltyTier; points: number }[]
}

// Referral
export interface ReferralResponse {
  id: number
  referrer_id: number
  referred_id: number
  status: ReferralStatus
  points_awarded_referrer: number
  points_awarded_referred: number
  converted_at?: string
  created_at: string
}

export interface ReferralRankingItem {
  client_id: number
  name: string
  code: string
  conversions: number
}

// Dashboard
export interface TodayAppointment {
  id: number
  scheduled_at: string
  ends_at: string
  status: AppointmentStatus
  client: { id: number; name: string; code: string; tier: LoyaltyTier }
  professional: { id: number; name: string }
  service: { id: number; name: string; duration_minutes: number }
  occasion?: string
}

export interface DashboardToday {
  date: string
  total_appointments: number
  status_breakdown: Record<string, number>
  revenue_today: number
  appointments: TodayAppointment[]
}

export interface DashboardKPIs {
  period: string
  since: string
  completed_appointments: number
  revenue: number
  active_clients: number
  points_issued: number
}

export interface WeeklyRevenueItem {
  date: string
  revenue: number
  appointments: number
}

export interface DashboardAlerts {
  birthdays_today: { id: number; name: string; code: string }[]
  platinum_today: { appointment_id: number; client_name: string; scheduled_at: string }[]
  low_stock: { id: number; name: string; unit: ProductUnit; stock_qty: number; min_stock: number }[]
  expiring_soon: { id: number; name: string; expiry_date: string; days_to_expiry: number }[]
}

// Reports
export interface RevenueReport {
  period_start: string
  period_end: string
  total_revenue: number
  total_appointments: number
  by_professional: { name: string; appointments: number; revenue: number }[]
  by_category: { name: string; appointments: number; revenue: number }[]
  by_gender: { gender: string; appointments: number; revenue: number }[]
}

export interface ClientReport {
  period_start: string
  period_end: string
  new_clients: number
  churn_risk_count: number
  tier_distribution: Record<LoyaltyTier, number>
  total_active: number
}

export interface LoyaltyMonthlyItem {
  month: string
  points_issued: number
  points_redeemed: number
}

export interface ReferralMonthlyItem {
  month: string
  referrals_created: number
  referrals_converted: number
  points_invested: number
  conversion_rate: number
}

// Estoque / Insumos
export type ProductUnit = 'ml' | 'g' | 'unit'
export type StockMovementType = 'purchase' | 'consumption' | 'loss' | 'adjustment'

export interface ProductResponse {
  id: number
  name: string
  unit: ProductUnit
  stock_qty: number
  min_stock: number
  expiry_date?: string
  cost_per_unit: number
  is_active: boolean
  created_at: string
}

export interface ProductCreate {
  name: string
  unit: ProductUnit
  stock_qty?: number
  min_stock?: number
  expiry_date?: string
  cost_per_unit?: number
}

export type ProductUpdate = Partial<{
  name: string
  unit: ProductUnit
  min_stock: number
  expiry_date: string
  cost_per_unit: number
  is_active: boolean
}>

export interface StockEntry {
  qty: number
  type: StockMovementType
  description?: string
}

export interface StockMovementResponse {
  id: number
  product_id: number
  appointment_id?: number
  type: StockMovementType
  qty: number
  qty_before: number
  qty_after: number
  description: string
  created_at: string
}

// Ficha técnica
export interface RecipeItem {
  product_id: number
  qty_consumed: number
}

export interface ServiceRecipeResponse {
  id: number
  service_id: number
  product_id: number
  product_name: string
  unit: ProductUnit
  qty_consumed: number
}
