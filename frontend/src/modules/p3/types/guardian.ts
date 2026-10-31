export type RiskSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type RiskCategory = 'BILLING' | 'PAYMENT' | 'SUBSCRIPTION' | 'REVENUE';
export type RiskStatus = 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface RiskAlertItem {
  id: string;
  rule_key: string;
  category: RiskCategory;
  severity: RiskSeverity;
  score: number;
  customer_id?: string | null;
  subscription_id?: string | null;
  invoice_id?: string | null;
  payment_id?: string | null;
  detected_at: string;
  estimated_impact: string;
  explanation: string;
  suggested_action: string;
  status: RiskStatus;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  resolution_note?: string | null;
}

export interface RiskAlertSummary {
  total_open_alerts: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_estimated_impact: string;
}

export interface RiskCategorySummary {
  category: string;
  count: number;
  estimated_impact: string;
}

export interface RiskDetectionRunItem {
  id: string;
  started_at: string;
  finished_at?: string | null;
  rules_run: number;
  alerts_created: number;
  status: string;
  error?: string | null;
}

export interface GuardianDashboardData {
  summary: RiskAlertSummary;
  categories_summary: RiskCategorySummary[];
  recent_runs: RiskDetectionRunItem[];
  top_alerts: RiskAlertItem[];
}

export interface AlertListResponse {
  items: RiskAlertItem[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}
