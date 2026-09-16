export interface FiscalParty {
  legal_name: string; tax_id: string; email: string | null
  street: string; number: string; district: string; postal_code: string
  city: string; municipality_code: string; state: string
}
export interface FiscalProfile extends FiscalParty {
  municipal_registration: string; tax_regime: 'mei' | 'simples' | 'normal'
  service_code: string; iss_rate: number | string
}
export interface FiscalDocument {
  id: number; tenant_id: number; issuer_kind: 'salon' | 'platform'
  source_key: string; appointment_id: number | null
  status: 'draft' | 'simulated' | 'cancelled'; environment: 'demo'; number: string | null
  competence: string; description: string; service_code: string
  amount: number; iss_rate: number; iss_amount: number
  issuer: FiscalProfile; recipient: FiscalParty
  created_at: string; issued_at: string | null; cancelled_at: string | null; cancellation_reason: string | null
}
export interface FiscalConfig { mode: 'disabled' | 'demo'; notice: string; real_issuance_available: false; can_manage_platform: boolean }
export interface FiscalAppointment { id: number; client_name: string; service_name: string; amount: number; competence: string }
export interface FiscalTenant { id: number; name: string; fiscal_profile: FiscalProfile | null }
export interface FiscalEvent { id: number; action: string; created_at: string }
export interface FiscalDraft {
  competence: string; description: string; service_code: string; iss_rate: number; recipient: FiscalParty
  appointment_id?: number; tenant_id?: number; subscription_reference?: string; amount?: number
}
