export interface DrilldownLink {
  label: string;
  url: string;
  filters: Record<string, any>;
}

export interface KpiMetric {
  value: string | number;
  previous: string | number;
  change_pct: number;
}

export interface FinanceOverviewData {
  kpis: {
    mrr: KpiMetric;
    arr: KpiMetric;
    active_subscriptions: KpiMetric;
    active_customers: KpiMetric;
    arpc: KpiMetric;
    revenue_received: KpiMetric;
    total_invoiced: KpiMetric;
    outstanding_balance: KpiMetric;
    overdue_amount: KpiMetric;
    overdue_count: KpiMetric;
    collection_rate_pct: KpiMetric;
    customer_churn_rate_pct: KpiMetric;
    new_subscriptions?: KpiMetric;
    renewals_count?: KpiMetric;
    churn_subscriptions?: KpiMetric;
  };
  period: {
    start: string;
    end: string;
    previous_start?: string;
    previous_end?: string;
  };
}

export interface RevenuePerformancePoint {
  period: string;
  invoiced: string;
  collected: string;
  collection_rate_pct: number;
  drilldown: DrilldownLink;
}

export interface FrequencyDistribution {
  frequency: string;
  count: number;
  mrr: string;
  percentage_subs: number;
  percentage_mrr: number;
  drilldown: DrilldownLink;
}

export interface PlanDistribution {
  plan_id: string;
  plan_name: string;
  frequency: string;
  count: number;
  mrr: string;
  percentage_mrr: number;
  drilldown: DrilldownLink;
}

export interface SubscriptionDistributionData {
  as_of_date: string;
  total_active_subscriptions: number;
  total_mrr: string;
  by_frequency: FrequencyDistribution[];
  by_plan: PlanDistribution[];
}

export interface AgingBucket {
  bucket: string;
  label: string;
  count: number;
  amount: string;
  percentage: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'SEVERE' | 'CRITICAL';
  drilldown: DrilldownLink;
}

export interface InvoiceAgingData {
  as_of_date: string;
  total_outstanding: string;
  buckets: AgingBucket[];
}

export interface SubscriptionGrowthPoint {
  period: string;
  new: number;
  renewed: number;
  closed: number;
  net_growth: number;
  drilldown: DrilldownLink;
}

export interface MrrTrendPoint {
  period: string;
  as_of_date: string;
  mrr: string;
  arr: string;
  rolling_avg_3m: string;
  growth_pct: number;
  drilldown: DrilldownLink;
}

export interface WaterfallStep {
  category: string;
  value: string;
  type: 'baseline' | 'positive' | 'negative' | 'total';
}

export interface MrrWaterfallData {
  starting_mrr: string;
  new_mrr: string;
  expansion_mrr: string;
  contraction_mrr: string;
  churn_mrr: string;
  ending_mrr: string;
  steps: WaterfallStep[];
  drilldown: DrilldownLink;
}

export interface FunnelStage {
  stage: string;
  label: string;
  count: number;
  amount: string;
  conversion_pct: number;
  dropoff_pct: number;
}

export interface CollectionFunnelData {
  period: { start: string; end: string };
  stages: FunnelStage[];
}

export interface CustomerShare {
  customer_id: string;
  customer_name: string;
  annual_invoiced: string;
  current_mrr: string;
  share_pct: number;
  cumulative_share_pct: number;
  drilldown: DrilldownLink;
}

export interface RevenueConcentrationData {
  total_annual_invoiced: string;
  total_active_mrr: string;
  top_customers: CustomerShare[];
  pareto_summary: {
    top_10_share_pct: number;
    risk_status: string;
  };
}

export interface CohortEntry {
  cohort: string;
  cohort_size: number;
  retention: (number | null)[];
  drilldown: DrilldownLink;
}

export interface CohortsData {
  intervals: string[];
  cohorts: CohortEntry[];
}

export interface ForecastPoint {
  month: string;
  mrr: string;
  arr: string;
  projected_invoiced: string;
  projected_collected: string;
  projected_outstanding: string;
}

export interface ForecastBaselineData {
  current_mrr: string;
  current_arr: string;
  horizon_months: number;
  baseline: ForecastPoint[];
}
