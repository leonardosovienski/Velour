export type PaymentMethod = 'pix' | 'cash' | 'debit_card' | 'credit_card' | 'other'
export type ExpenseCategory = 'rent' | 'supplies' | 'utilities' | 'people' | 'other'
export interface ExpenseInput { description: string; category: ExpenseCategory; amount: number; due_date: string; paid_on: string | null }
export interface Expense extends ExpenseInput { id: number }
export interface Receipt { id: number; client: string; service: string; date: string; amount: number; received: number; remaining: number; payment_method: PaymentMethod | null; document_id: number | null; document_status: 'draft' | 'simulated' | 'cancelled' | null }
export interface FinanceOverview { month: string; received: number; receivable: number; expenses_paid: number; expenses_pending: number; balance: number; receipts: Receipt[]; expenses: Expense[] }
export interface DreRow { label: string; value: number; level: number }
export interface JournalEntry { date: string; history: string; debit: string; credit: string; amount: number }
export interface TrialBalanceRow { code: string; name: string; debit: number; credit: number; balance: number; nature: 'D' | 'C' }
export interface AccountingReport { month: string; notice: string; iss_rate: number; dre: DreRow[]; entries: JournalEntry[]; trial_balance: TrialBalanceRow[]; total_debit: number; total_credit: number; result: number; chart_of_accounts: { code: string; name: string; nature: 'D' | 'C' }[] }
export type CostCategory = 'inputs' | 'commissions' | 'taxes' | 'rent' | 'supplies' | 'utilities' | 'people' | 'other'
export interface CostSummary { appointments: number; revenue: number; variable_costs: number; contribution_margin: number; contribution_margin_ratio: number | null; fixed_costs: number; result: number; average_ticket: number | null; cost_per_appointment: number | null; break_even_revenue: number | null; break_even_appointments: number | null; safety_margin: number | null }
export interface CostLine { category: CostCategory; label: string; kind: 'variable' | 'fixed'; actual: number; budget: number | null; variance: number | null; consumed_ratio: number | null; status: 'within' | 'over' | 'no_budget' }
export interface CostCenter { id: number; name: string; appointments: number; revenue: number; inputs: number; commissions: number; taxes: number; contribution_margin: number; margin_ratio: number | null }
export interface ServiceCost extends CostCenter { category: string }
export interface ProfessionalCost extends CostCenter { commission_rate: number }
export interface StandardCost { id: number; name: string; price: number; recipe_items: number; standard_input_cost: number; input_ratio: number | null; taxes: number; margin_before_commission: number }
export interface CostHistoryItem { month: string; appointments: number; revenue: number; variable_costs: number; fixed_costs: number; result: number }
export interface CostReport { month: string; notice: string; iss_rate: number; summary: CostSummary; lines: CostLine[]; budget_total: number | null; services: ServiceCost[]; professionals: ProfessionalCost[]; standard_costs: StandardCost[]; history: CostHistoryItem[]; alerts: { level: 'warning' | 'danger'; message: string }[] }
export interface CostBudgetItem { category: CostCategory; amount: number }
