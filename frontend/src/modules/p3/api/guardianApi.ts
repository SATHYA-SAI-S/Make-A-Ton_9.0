import {
  GuardianDashboardData,
  AlertListResponse,
  RiskAlertItem,
  RiskDetectionRunItem,
} from '../types/guardian';

const BASE_URL = '/api/v1/guardian';

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

export const guardianApi = {
  async getDashboard(): Promise<GuardianDashboardData> {
    const res = await fetch(`${BASE_URL}/dashboard`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch guardian dashboard: ${res.statusText}`);
    return res.json();
  },

  async listAlerts(params: {
    status?: string;
    severity?: string;
    category?: string;
    rule_key?: string;
    customer_id?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<AlertListResponse> {
    const res = await fetch(`${BASE_URL}/alerts${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to list alerts: ${res.statusText}`);
    return res.json();
  },

  async getAlertDetail(alertId: string): Promise<RiskAlertItem> {
    const res = await fetch(`${BASE_URL}/alerts/${alertId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch alert detail: ${res.statusText}`);
    return res.json();
  },

  async executeAlertAction(
    alertId: string,
    action: 'ACKNOWLEDGE' | 'RESOLVE' | 'DISMISS',
    note?: string
  ): Promise<{ message: string; id: string; status: string }> {
    const res = await fetch(`${BASE_URL}/alerts/${alertId}/action`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ action, note }),
    });
    if (!res.ok) throw new Error(`Failed to execute alert action: ${res.statusText}`);
    return res.json();
  },

  async triggerDetectionRun(rules?: string[]): Promise<RiskDetectionRunItem> {
    const res = await fetch(`${BASE_URL}/run`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ rules: rules || null }),
    });
    if (!res.ok) throw new Error(`Failed to trigger detection run: ${res.statusText}`);
    return res.json();
  },

  async getRecentRuns(limit = 20): Promise<RiskDetectionRunItem[]> {
    const res = await fetch(`${BASE_URL}/runs?limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch detection runs: ${res.statusText}`);
    return res.json();
  },
};
