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
