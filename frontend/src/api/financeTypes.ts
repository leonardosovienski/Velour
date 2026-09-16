export type PaymentMethod = 'pix' | 'cash' | 'debit_card' | 'credit_card' | 'other'
export type ExpenseCategory = 'rent' | 'supplies' | 'utilities' | 'people' | 'other'
export interface ExpenseInput { description: string; category: ExpenseCategory; amount: number; due_date: string; paid_on: string | null }
export interface Expense extends ExpenseInput { id: number }
export interface Receipt { id: number; client: string; service: string; date: string; amount: number; received: number; remaining: number; payment_method: PaymentMethod | null; document_id: number | null; document_status: 'draft' | 'simulated' | 'cancelled' | null }
export interface FinanceOverview { month: string; received: number; receivable: number; expenses_paid: number; expenses_pending: number; balance: number; receipts: Receipt[]; expenses: Expense[] }
