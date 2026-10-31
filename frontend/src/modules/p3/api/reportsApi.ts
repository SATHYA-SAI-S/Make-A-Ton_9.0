import { ReportMetadata, ReportResult } from '../types/reports';

const BASE_URL = '/api/v1/reports';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token') || 'dev-admin-token';
  return {
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

export const reportsApi = {
  async getCatalog(): Promise<{ reports: ReportMetadata[] }> {
    const res = await fetch(`${BASE_URL}/catalog`, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch report catalog: ${res.statusText}`);
    }
    return res.json();
  },

  async getReportData(reportId: string, params: Record<string, any> = {}): Promise<ReportResult> {
    const res = await fetch(`${BASE_URL}/${reportId}${buildQuery({ ...params, format: 'json' })}`, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to load report data: ${res.statusText}`);
    }
    return res.json();
  },

  async downloadReport(reportId: string, format: 'csv' | 'pdf', params: Record<string, any> = {}): Promise<void> {
    const url = `${BASE_URL}/${reportId}${buildQuery({ ...params, format })}`;
    const res = await fetch(url, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Download failed with status ${res.status}: ${res.statusText}`);
    }

    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', `${reportId}_${new Date().toISOString().slice(0, 10)}.${format}`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  },
};
