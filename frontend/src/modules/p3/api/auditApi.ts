import { AuditLog, AuditPageResponse, AuditQueryParams } from '../types/audit';

const BASE_URL = '/api/v1/audit';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token') || 'dev-admin-token';
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
}

function buildQuery(params: Record<string, any>): string {
  const q = new URLSearchParams();
  for (const [key, val] of Object.entries(params)) {
    if (val !== undefined && val !== null && val !== '' && val !== 'ALL') {
      q.set(key, String(val));
    }
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

export const auditApi = {
  async getLogs(params: AuditQueryParams = {}): Promise<AuditPageResponse> {
    const res = await fetch(`${BASE_URL}/logs${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch audit logs: ${res.statusText}`);
    }
    return res.json();
  },

  async getLogDetail(id: string): Promise<AuditLog> {
    const res = await fetch(`${BASE_URL}/logs/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch audit log detail: ${res.statusText}`);
    }
    return res.json();
  },

  async getPriceHistory(params: { product_id?: string; page?: number; page_size?: number } = {}): Promise<AuditPageResponse> {
    const res = await fetch(`${BASE_URL}/views/price-history${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch price history: ${res.statusText}`);
    }
    return res.json();
  },

  async getPlanHistory(params: { plan_id?: string; page?: number; page_size?: number } = {}): Promise<AuditPageResponse> {
    const res = await fetch(`${BASE_URL}/views/plan-history${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch plan history: ${res.statusText}`);
    }
    return res.json();
  },

  async getInvoiceCancellations(params: { page?: number; page_size?: number } = {}): Promise<AuditPageResponse> {
    const res = await fetch(`${BASE_URL}/views/invoice-cancellations${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch cancellations: ${res.statusText}`);
    }
    return res.json();
  },

  async getSubscriptionLifecycle(params: { subscription_id?: string; page?: number; page_size?: number } = {}): Promise<AuditPageResponse> {
    const res = await fetch(`${BASE_URL}/views/subscription-lifecycle${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch lifecycle history: ${res.statusText}`);
    }
    return res.json();
  },
};
