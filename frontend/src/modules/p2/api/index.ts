import {
  TaxRule,
  BillingSettings,
  DiscountRule,
  BillingRun,
  BillingRunItem,
  Invoice,
  Payment,
  OverdueInvoice,
  OverdueSummary,
  PaymentFollowup,
  ReconciliationReport
} from '../types';

const BASE_URL = import.meta.env?.VITE_API_BASE_URL || '/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson?.error?.message || errJson?.detail || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  // Handle binary/empty responses
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/pdf')) {
    return (await response.blob()) as unknown as T;
  }
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// 1. Taxes API
export const taxApi = {
  getRules: () => request<TaxRule[]>('/taxes/rules'),
  createRule: (rule: Partial<TaxRule>) =>
    request<TaxRule>('/taxes/rules', { method: 'POST', body: JSON.stringify(rule) }),
  getSettings: () => request<BillingSettings>('/taxes/settings'),
  updateSettings: (settings: Partial<BillingSettings>) =>
    request<BillingSettings>('/taxes/settings', { method: 'PUT', body: JSON.stringify(settings) }),
  previewTax: (payload: { customer_id?: string; customer_state_code: string; lines: any[] }) =>
    request<any>('/taxes/preview', { method: 'POST', body: JSON.stringify(payload) })
};

// 2. Discounts API
export const discountApi = {
  getDiscounts: () => request<DiscountRule[]>('/discounts'),
  createDiscount: (discount: Partial<DiscountRule>) =>
    request<DiscountRule>('/discounts', { method: 'POST', body: JSON.stringify(discount) }),
  deleteDiscount: (id: string) =>
    request<void>(`/discounts/${id}`, { method: 'DELETE' }),
  getPerformance: () => request<any>('/discounts/performance')
};

// 3. Billing Engine API
export const billingApi = {
  runBilling: (payload: { as_of?: string; dry_run?: boolean }) =>
    request<BillingRun>('/billing/run', { method: 'POST', body: JSON.stringify(payload) }),
  getRuns: (page = 1, pageSize = 20) =>
    request<{ items: BillingRun[]; total: number }>(`/billing/runs?page=${page}&page_size=${pageSize}`),
  getRun: (id: string) => request<BillingRun & { items: BillingRunItem[] }>(`/billing/runs/${id}`)
};

// 4. Invoices API
export const invoiceApi = {
  getInvoices: (params: { customer_id?: string; status?: string; page?: number; page_size?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.customer_id) qs.set('customer_id', params.customer_id);
    if (params.status) qs.set('status', params.status);
    if (params.page) qs.set('page', String(params.page));
    if (params.page_size) qs.set('page_size', String(params.page_size));
    return request<{ items: Invoice[]; total: number; page: number; page_size: number }>(`/invoices?${qs.toString()}`);
  },
  getInvoice: (id: string) => request<Invoice>(`/invoices/${id}`),
  confirmInvoice: (id: string) =>
    request<Invoice>(`/invoices/${id}/confirm`, { method: 'POST' }),
  cancelInvoice: (id: string, reason: string) =>
    request<Invoice>(`/invoices/${id}/cancel`, { method: 'POST', body: JSON.stringify({ reason }) }),
  getPdf: (id: string) => request<Blob>(`/invoices/${id}/pdf`),
  getPrintableUrl: (id: string) => `${BASE_URL}/invoices/${id}/printable`
};

// 5. Payments API
export const paymentApi = {
  recordPayment: (payload: {
    customer_id: string;
    method: string;
    amount: string;
    reference?: string;
    notes?: string;
    allocations?: { invoice_id: string; amount: string }[];
  }) => request<Payment>('/payments', { method: 'POST', body: JSON.stringify(payload) }),
  getPayments: (params: { customer_id?: string; status?: string; page?: number; page_size?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.customer_id) qs.set('customer_id', params.customer_id);
    if (params.status) qs.set('status', params.status);
    if (params.page) qs.set('page', String(params.page));
    if (params.page_size) qs.set('page_size', String(params.page_size));
    return request<{ items: Payment[]; total: number }>(`/payments?${qs.toString()}`);
  },
  getPayment: (id: string) => request<Payment>(`/payments/${id}`),
  allocatePayment: (id: string, allocations: { invoice_id: string; amount: string }[]) =>
    request<Payment>(`/payments/${id}/allocate`, { method: 'POST', body: JSON.stringify({ allocations }) }),
  refundPayment: (id: string, amount: string, reason?: string) =>
    request<any>(`/payments/${id}/refund`, { method: 'POST', body: JSON.stringify({ amount, reason }) }),
  getCustomerOutstanding: (customerId: string) =>
    request<{ customer_id: string; outstanding_balance: string }>(`/payments/customer/${customerId}/outstanding`),
  createOrder: (payload: { amount: string; currency?: string; invoice_id?: string; customer_id?: string }) =>
    request<any>('/payments/create-order', { method: 'POST', body: JSON.stringify(payload) })
};

// 6. Overdue & Reminders API
export const overdueApi = {
  getOverdueInvoices: (asOf?: string) => {
    const qs = asOf ? `?as_of=${asOf}` : '';
    return request<OverdueInvoice[]>(`/overdue/invoices${qs}`);
  },
  getSummary: (asOf?: string) => {
    const qs = asOf ? `?as_of=${asOf}` : '';
    return request<OverdueSummary>(`/overdue/summary${qs}`);
  },
  triggerReminders: (asOf?: string) =>
    request<{ as_of: string; invoices_evaluated: number; reminders_sent: number; reminders_skipped: number }>(
      '/overdue/trigger-reminders',
      { method: 'POST', body: JSON.stringify(asOf ? { as_of: asOf } : {}) }
    ),
  createFollowup: (payload: {
    invoice_id: string;
    notes: string;
    promised_payment_date?: string;
    channel?: string;
    status?: string;
  }) => request<PaymentFollowup>('/overdue/followups', { method: 'POST', body: JSON.stringify(payload) }),
  getFollowups: (invoiceId: string) => request<PaymentFollowup[]>(`/overdue/followups/${invoiceId}`)
};

// 7. Reconciliation API
export const reconciliationApi = {
  getReport: () => request<ReconciliationReport>('/reconciliation/report'),
  autoAllocate: (customerId?: string) =>
    request<{ status: string; allocations_made: number; total_allocated: string }>(
      '/reconciliation/allocate-unallocated',
      { method: 'POST', body: JSON.stringify(customerId ? { customer_id: customerId } : {}) }
    )
};
