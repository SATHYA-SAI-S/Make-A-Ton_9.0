export interface AuditFieldDiff {
  before: any;
  after: any;
  changed: boolean;
}

export interface AuditLog {
  id: string;
  occurred_at: string;
  actor_id: string;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string;
  before?: Record<string, any> | null;
  after?: Record<string, any> | null;
  meta?: Record<string, any> | null;
  request_id?: string | null;
  diff?: Record<string, AuditFieldDiff>;
}

export interface AuditQueryParams {
  actor_id?: string;
  actor_role?: string;
  action?: string;
  entity_type?: string;
  entity_id?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface AuditPageResponse {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
