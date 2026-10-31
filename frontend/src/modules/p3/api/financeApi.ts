import {
  FinanceOverviewData,
  RevenuePerformancePoint,
  SubscriptionDistributionData,
  InvoiceAgingData,
  SubscriptionGrowthPoint,
  MrrTrendPoint,
  MrrWaterfallData,
  CollectionFunnelData,
  RevenueConcentrationData,
  CohortsData,
  ForecastBaselineData,
  ForecastAssumptions,
  ForecastSimulationResult,
  SavedForecastScenario,
} from '../types/finance';

const BASE_URL = '/api/v1/finance';

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

export const financeApi = {
  async getOverview(params: {
    start_date?: string;
    end_date?: string;
    plan_id?: string;
    frequency?: string;
    customer_id?: string;
    status?: string;
  } = {}): Promise<FinanceOverviewData> {
    const res = await fetch(`${BASE_URL}/overview${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch finance overview: ${res.statusText}`);
    return res.json();
  },

  async getRevenuePerformance(params: {
    start_date?: string;
    end_date?: string;
    customer_id?: string;
  } = {}): Promise<RevenuePerformancePoint[]> {
    const res = await fetch(`${BASE_URL}/charts/revenue-performance${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch revenue performance: ${res.statusText}`);
    return res.json();
  },

  async getSubscriptionDistribution(params: {
    as_of?: string;
    customer_id?: string;
  } = {}): Promise<SubscriptionDistributionData> {
    const res = await fetch(`${BASE_URL}/charts/subscription-distribution${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch subscription distribution: ${res.statusText}`);
    return res.json();
  },

  async getInvoiceAging(params: {
    as_of?: string;
    customer_id?: string;
  } = {}): Promise<InvoiceAgingData> {
    const res = await fetch(`${BASE_URL}/charts/invoice-aging${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch invoice aging: ${res.statusText}`);
    return res.json();
  },

  async getSubscriptionGrowth(params: {
    start_date?: string;
    end_date?: string;
  } = {}): Promise<SubscriptionGrowthPoint[]> {
    const res = await fetch(`${BASE_URL}/charts/subscription-growth${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch subscription growth: ${res.statusText}`);
    return res.json();
  },

  async getMrrTrend(params: {
    start_date?: string;
    end_date?: string;
    plan_id?: string;
    customer_id?: string;
  } = {}): Promise<MrrTrendPoint[]> {
    const res = await fetch(`${BASE_URL}/charts/mrr-trend${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch MRR trend: ${res.statusText}`);
    return res.json();
  },

  async getMrrWaterfall(params: {
    start_date?: string;
    end_date?: string;
  } = {}): Promise<MrrWaterfallData> {
    const res = await fetch(`${BASE_URL}/charts/mrr-waterfall${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch MRR waterfall: ${res.statusText}`);
    return res.json();
  },

  async getCohorts(lookback_months = 6): Promise<CohortsData> {
    const res = await fetch(`${BASE_URL}/charts/cohorts?lookback_months=${lookback_months}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch cohort retention: ${res.statusText}`);
    return res.json();
  },

  async getRevenueConcentration(top_n = 10): Promise<RevenueConcentrationData> {
    const res = await fetch(`${BASE_URL}/charts/concentration?top_n=${top_n}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch revenue concentration: ${res.statusText}`);
    return res.json();
  },

  async getCollectionFunnel(params: {
    start_date?: string;
    end_date?: string;
    customer_id?: string;
  } = {}): Promise<CollectionFunnelData> {
    const res = await fetch(`${BASE_URL}/charts/collection-funnel${buildQuery(params)}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch collection funnel: ${res.statusText}`);
    return res.json();
  },

  async getForecastBaseline(horizon_months = 12): Promise<ForecastBaselineData> {
    const res = await fetch(`${BASE_URL}/charts/forecast?horizon_months=${horizon_months}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch forecast baseline: ${res.statusText}`);
    return res.json();
  },

  async simulateForecast(body: {
    horizon_months?: number;
    assumptions?: Partial<ForecastAssumptions>;
    starting_mrr?: number;
  }): Promise<ForecastSimulationResult> {
    const res = await fetch(`${BASE_URL}/forecast/simulate`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        horizon_months: body.horizon_months ?? 12,
        assumptions: body.assumptions ?? {},
        starting_mrr: body.starting_mrr,
      }),
    });
    if (!res.ok) throw new Error(`Failed to simulate forecast: ${res.statusText}`);
    return res.json();
  },

  async getForecastBaselineDetailed(horizon_months = 12): Promise<ForecastSimulationResult> {
    const res = await fetch(`${BASE_URL}/forecast/baseline?horizon_months=${horizon_months}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch forecast baseline: ${res.statusText}`);
    return res.json();
  },

  async saveForecastScenario(scenario: {
    name: string;
    description?: string;
    horizon_months: number;
    assumptions?: Partial<ForecastAssumptions>;
  }): Promise<SavedForecastScenario> {
    const res = await fetch(`${BASE_URL}/forecast/scenarios`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(scenario),
    });
    if (!res.ok) throw new Error(`Failed to save scenario: ${res.statusText}`);
    return res.json();
  },

  async listForecastScenarios(): Promise<SavedForecastScenario[]> {
    const res = await fetch(`${BASE_URL}/forecast/scenarios`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to list scenarios: ${res.statusText}`);
    return res.json();
  },

  async getForecastScenario(id: string): Promise<SavedForecastScenario> {
    const res = await fetch(`${BASE_URL}/forecast/scenarios/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to get scenario: ${res.statusText}`);
    return res.json();
  },

  async deleteForecastScenario(id: string): Promise<{ message: string; id: string }> {
    const res = await fetch(`${BASE_URL}/forecast/scenarios/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to delete scenario: ${res.statusText}`);
    return res.json();
  },

  getExportUrl(chart: string, params: Record<string, any> = {}): string {
    const q = buildQuery({ chart, format: 'csv', ...params });
    return `${BASE_URL}/export${q}`;
  },
};
