import {
  CustomerProfile,
  DashboardSummary,
  Subscription,
  Invoice,
  Payment,
  CustomerRequest,
} from '../types/portal';

const BASE_URL = '/api/v1/portal';

// Default customer bearer token for local demo
let currentAuthToken = 'Bearer dev-customer-token';

export function setAuthToken(token: string) {
  currentAuthToken = token.startsWith('Bearer ') ? token : `Bearer ${token}`;
}

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: currentAuthToken,
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const errorJson = await response.json().catch(() => ({}));
    throw new Error(errorJson?.error?.message || `API error ${response.status}: ${response.statusText}`);
  }
  return response;
}

export const portalApi = {
  async getDashboard(): Promise<DashboardSummary> {
    const res = await fetchWithAuth(`${BASE_URL}/dashboard`);
    return res.json();
  },

  async getSubscriptions(status?: string): Promise<Subscription[]> {
    const q = status && status !== 'ALL' ? `?status=${status}` : '';
    const res = await fetchWithAuth(`${BASE_URL}/subscriptions${q}`);
    return res.json();
  },

  async getSubscriptionDetail(id: string): Promise<Subscription> {
    const res = await fetchWithAuth(`${BASE_URL}/subscriptions/${id}`);
    return res.json();
  },

  async getInvoices(status?: string): Promise<Invoice[]> {
    const q = status && status !== 'ALL' ? `?status=${status}` : '';
    const res = await fetchWithAuth(`${BASE_URL}/invoices${q}`);
    return res.json();
  },

  async getInvoiceDetail(id: string): Promise<Invoice> {
    const res = await fetchWithAuth(`${BASE_URL}/invoices/${id}`);
    return res.json();
  },

  async downloadInvoicePdf(id: string, invoiceNumber?: string): Promise<void> {
    const res = await fetchWithAuth(`${BASE_URL}/invoices/${id}/pdf`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Invoice_${invoiceNumber || id}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  },

  async getPayments(): Promise<Payment[]> {
    const res = await fetchWithAuth(`${BASE_URL}/payments`);
    return res.json();
  },

  async getBalance(): Promise<{ outstanding_balance: string; currency: string; has_unpaid_invoices: boolean; unpaid_count: number }> {
    const res = await fetchWithAuth(`${BASE_URL}/balance`);
    return res.json();
  },

  async getProfile(): Promise<CustomerProfile> {
    const res = await fetchWithAuth(`${BASE_URL}/profile`);
    return res.json();
  },

  async updateProfile(payload: { phone?: string; billing_address?: string }): Promise<CustomerProfile> {
    const res = await fetchWithAuth(`${BASE_URL}/profile`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async submitRequest(payload: {
    subscription_id: string;
    type: string;
    target_plan_id?: string;
    note?: string;
  }): Promise<CustomerRequest> {
    const res = await fetchWithAuth(`${BASE_URL}/requests`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  async getMyRequests(status?: string): Promise<{ items: CustomerRequest[]; total: number }> {
    const q = status && status !== 'ALL' ? `?status=${status}` : '';
    const res = await fetchWithAuth(`${BASE_URL}/requests${q}`);
    return res.json();
  },
};
