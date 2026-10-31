export interface CustomerProfile {
  id: string;
  user_id: string;
  name: string;
  email: string;
  phone?: string;
  billing_address?: string;
  state_code?: string;
  gstin?: string;
  status: 'ACTIVE' | 'INACTIVE' | 'BLOCKED';
  segment: 'ENTERPRISE' | 'MID_MARKET' | 'STARTER';
}

export interface SubscriptionLine {
  id: string;
  product_id: string;
  variant_id?: string;
  product_name: string;
  quantity: number;
  unit_price: string;
  amount: string;
}

export interface Subscription {
  id: string;
  number: string;
  customer_id: string;
  plan_id: string;
  plan_name: string;
  status: 'DRAFT' | 'QUOTATION' | 'CONFIRMED' | 'ACTIVE' | 'PAUSED' | 'CLOSED';
  close_reason?: string;
  start_date: string;
  expiry_date?: string;
  next_billing_date?: string;
  payment_terms_days: number;
  billing_frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY';
  currency: string;
  lines: SubscriptionLine[];
  timeline?: { date: string; event: string }[];
}

export interface InvoiceLine {
  id: string;
  product_id: string;
  description: string;
  quantity: number;
  unit_price: string;
  discount_amount: string;
  tax_rate: string;
  tax_amount: string;
  line_total: string;
}

export interface Invoice {
  id: string;
  number: string;
  customer_id: string;
  subscription_id: string;
  status: 'DRAFT' | 'CONFIRMED' | 'PARTIALLY_PAID' | 'PAID' | 'CANCELLED';
  invoice_date: string;
  due_date: string;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  total: string;
  amount_paid: string;
  balance: string;
  is_overdue?: boolean;
  lines: InvoiceLine[];
}

export interface Payment {
  id: string;
  customer_id: string;
  method: 'UPI' | 'CARD' | 'BANK_TRANSFER' | 'CASH' | 'OTHER';
  amount: string;
  payment_date: string;
  reference: string;
  status: 'RECORDED' | 'FAILED' | 'REFUNDED';
  notes?: string;
}

export interface CustomerRequest {
  id: string;
  customer_id: string;
  subscription_id: string;
  type: 'UPGRADE' | 'DOWNGRADE' | 'PAUSE' | 'CANCEL' | 'RENEWAL';
  target_plan_id?: string;
  note?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'APPLIED' | 'FAILED';
  decided_by?: string;
  decided_at?: string;
  decision_note?: string;
  created_at: string;
}

export interface DashboardSummary {
  customer: CustomerProfile;
  active_subscriptions_count: number;
  outstanding_balance: string;
  unpaid_invoices_count: number;
  next_renewal_date?: string;
  recent_subscriptions: Subscription[];
  recent_invoices: Invoice[];
}
