export type TaxType = 'GST' | 'CGST' | 'SGST' | 'IGST' | 'VAT' | 'CUSTOM';

export interface TaxRule {
  id: string;
  name: string;
  rate: string;
  type: TaxType;
  effective_from: string;
  effective_to: string | null;
  active: boolean;
  product_ids?: string[];
  created_at?: string;
}

export interface BillingSettings {
  id: string;
  company_name: string;
  company_state_code: string;
  company_gstin: string;
  default_currency: string;
  invoice_prefix: string;
  invoice_sequence: number;
}

export type DiscountType = 'PERCENTAGE' | 'FIXED';
export type DiscountScope = 'PRODUCT' | 'SUBSCRIPTION';

export interface DiscountRule {
  id: string;
  code: string;
  name: string;
  discount_type: DiscountType;
  value: string;
  scope: DiscountScope;
  max_discount_amount: string | null;
  max_uses: number | null;
  current_uses: number;
  valid_from: string;
  valid_until: string | null;
  active: boolean;
  product_ids?: string[];
}

export interface BillingRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'PARTIAL_FAILURE' | 'FAILED';
  triggered_by: string;
  subscriptions_checked: number;
  invoices_created: number;
  failures: number;
}

export interface BillingRunItem {
  id: string;
  run_id: string;
  subscription_id: string;
  period_start: string;
  period_end: string;
  invoice_id: string | null;
  result: 'SUCCESS' | 'DRY_RUN' | 'SKIPPED' | 'FAILED';
  error: string | null;
}

export type InvoiceStatus = 'DRAFT' | 'CONFIRMED' | 'PARTIALLY_PAID' | 'PAID' | 'CANCELLED';

export interface InvoiceLine {
  id: string;
  product_id: string;
  variant_id: string | null;
  description: string;
  quantity: string;
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
  subscription_id: string | null;
  status: InvoiceStatus;
  invoice_date: string;
  due_date: string;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  total: string;
  amount_paid: string;
  balance: string;
  currency: string;
  is_overdue?: boolean;
  cancellation_reason?: string | null;
  lines?: InvoiceLine[];
  snapshot?: any;
  created_at: string;
}

export type PaymentMethod = 'UPI' | 'CARD' | 'BANK_TRANSFER' | 'CASH' | 'OTHER';
export type PaymentStatus = 'RECORDED' | 'FAILED' | 'REFUNDED';

export interface PaymentAllocation {
  id: string;
  payment_id: string;
  invoice_id: string;
  amount: string;
  created_at: string;
}

export interface PaymentRefund {
  id: string;
  payment_id: string;
  amount: string;
  reason: string | null;
  created_at: string;
}

export interface Payment {
  id: string;
  customer_id: string;
  method: PaymentMethod;
  amount: string;
  unallocated_amount: string;
  payment_date: string;
  reference: string | null;
  notes: string | null;
  status: PaymentStatus;
  gateway_event_id?: string | null;
  allocations?: PaymentAllocation[];
  refunds?: PaymentRefund[];
}

export interface OverdueInvoice {
  invoice_id: string;
  invoice_number: string;
  customer_id: string;
  customer_name: string;
  customer_email: string | null;
  due_date: string;
  days_overdue: number;
  tier: 1 | 2 | 3;
  total: string;
  amount_paid: string;
  balance: string;
  status: string;
}

export interface OverdueSummary {
  as_of: string;
  total_overdue_count: number;
  total_overdue_amount: string;
  tiers: {
    tier_1: { count: number; amount: string };
    tier_2: { count: number; amount: string };
    tier_3: { count: number; amount: string };
  };
}

export interface PaymentFollowup {
  id: string;
  invoice_id: string;
  customer_id: string;
  tier: number | null;
  channel: string;
  notes: string | null;
  promised_payment_date: string | null;
  status: 'PENDING' | 'PROMISED' | 'DISPUTED' | 'RESOLVED';
  created_at: string;
}

export interface DiscrepancyItem {
  type: string;
  entity_id: string;
  description: string;
}

export interface ReconciliationReport {
  timestamp: string;
  is_healthy: boolean;
  discrepancies_count: number;
  total_payments_checked: number;
  total_invoices_checked: number;
  metrics: {
    total_payment_volume: string;
    total_unallocated_volume: string;
    total_invoice_balance: string;
    total_invoice_paid: string;
  };
  discrepancies: DiscrepancyItem[];
}
