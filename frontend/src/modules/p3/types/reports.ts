export interface ReportMetadata {
  id: string;
  name: string;
  description: string;
  supported_formats: string[];
}

export interface ReportResult {
  title: string;
  subtitle: string;
  headers: string[];
  rows: (string | number)[][];
  summary?: Record<string, string>;
}

export interface ReportFilterState {
  startDate: string;
  endDate: string;
  asOfDate: string;
  status: string;
  planId: string;
}
