import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  TrendingUp,
  DollarSign,
  Users,
  Repeat,
  AlertTriangle,
  FileText,
  Calendar,
  Percent,
  Download,
  ArrowRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

import { StatCard } from '@/shared/ui/StatCard';
import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { FilterBar, AnalyticsFilters } from '../../charts/FilterBar';
import { financeApi } from '../../api/financeApi';
import { FinanceOverviewData, RevenuePerformancePoint, MrrTrendPoint } from '../../types/finance';

export const FinanceOverview: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Filters state initialized from URL search params
  const [filters, setFilters] = useState<AnalyticsFilters>({
    dateRange: {
      startDate: searchParams.get('start_date') || new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0],
      endDate: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
    },
    frequency: searchParams.get('frequency') || 'ALL',
    planId: searchParams.get('plan_id') || 'ALL',
    status: searchParams.get('status') || 'ALL',
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [overview, setOverview] = useState<FinanceOverviewData | null>(null);
  const [revPerf, setRevPerf] = useState<RevenuePerformancePoint[]>([]);
  const [mrrTrend, setMrrTrend] = useState<MrrTrendPoint[]>([]);

  // Synchronize state with URL query parameters
  const updateFilters = (newFilters: AnalyticsFilters) => {
    setFilters(newFilters);
    const params = new URLSearchParams();
    if (newFilters.dateRange.startDate) params.set('start_date', newFilters.dateRange.startDate);
    if (newFilters.dateRange.endDate) params.set('end_date', newFilters.dateRange.endDate);
    if (newFilters.frequency !== 'ALL') params.set('frequency', newFilters.frequency);
    if (newFilters.planId !== 'ALL') params.set('plan_id', newFilters.planId);
    if (newFilters.status !== 'ALL') params.set('status', newFilters.status);
    setSearchParams(params);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [overviewData, revData, mrrData] = await Promise.all([
        financeApi.getOverview({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
          frequency: filters.frequency,
          plan_id: filters.planId,
          status: filters.status,
        }),
        financeApi.getRevenuePerformance({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
        }),
        financeApi.getMrrTrend({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
        }),
      ]);
      setOverview(overviewData);
      setRevPerf(revData);
      setMrrTrend(mrrData);
    } catch (err) {
      console.error('Error loading finance overview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  const kpis = overview?.kpis;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Finance Intelligence Overview
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Real-time financial performance, MRR normalization, and cash collections
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('revenue-performance', { start_date: filters.dateRange.startDate, end_date: filters.dateRange.endDate }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/p3/finance/revenue')}
            className="flex items-center gap-1.5"
          >
            Deep Dive
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Reactive Filter Bar */}
      <FilterBar
        filters={filters}
        onChange={updateFilters}
        onReset={() => updateFilters({
          dateRange: {
            startDate: new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0],
            endDate: new Date().toISOString().split('T')[0],
          },
          frequency: 'ALL',
          planId: 'ALL',
          status: 'ALL',
        })}
      />

      {/* Core KPI StatCards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Monthly Recurring Revenue (MRR)"
          value={`₹${kpis?.mrr?.value || '0.00'}`}
          change={kpis?.mrr?.change_pct}
          trend={Number(kpis?.mrr?.change_pct || 0) >= 0 ? 'up' : 'down'}
          icon={<DollarSign className="w-5 h-5 text-indigo-600" />}
          description="Normalized monthly active recurring revenue"
          loading={loading}
          onClick={() => navigate(`/p3/finance/subscriptions?status=ACTIVE`)}
        />
        <StatCard
          title="Annual Recurring Revenue (ARR)"
          value={`₹${kpis?.arr?.value || '0.00'}`}
          change={kpis?.arr?.change_pct}
          trend={Number(kpis?.arr?.change_pct || 0) >= 0 ? 'up' : 'down'}
          icon={<TrendingUp className="w-5 h-5 text-emerald-600" />}
          description="MRR × 12 annualized run rate"
          loading={loading}
        />
        <StatCard
          title="Cash Inflow (Net Revenue)"
          value={`₹${kpis?.revenue_received?.value || '0.00'}`}
          change={kpis?.revenue_received?.change_pct}
          trend={Number(kpis?.revenue_received?.change_pct || 0) >= 0 ? 'up' : 'down'}
          icon={<DollarSign className="w-5 h-5 text-blue-600" />}
          description="Recorded payments minus refunds"
          loading={loading}
          onClick={() => navigate(`/p3/finance/invoices?period=${overview?.period.start}`)}
        />
        <StatCard
          title="Collection Rate %"
          value={`${kpis?.collection_rate_pct?.value || '0.00'}%`}
          change={kpis?.collection_rate_pct?.change_pct}
          trend={Number(kpis?.collection_rate_pct?.change_pct || 0) >= 0 ? 'up' : 'down'}
          icon={<Percent className="w-5 h-5 text-purple-600" />}
          description="Collected amount / due amount"
          loading={loading}
          onClick={() => navigate('/p3/finance/collections')}
        />
      </div>

      {/* Secondary KPI StatCards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Subscriptions"
          value={String(kpis?.active_subscriptions?.value || 0)}
          change={kpis?.active_subscriptions?.change_pct}
          trend={Number(kpis?.active_subscriptions?.change_pct || 0) >= 0 ? 'up' : 'down'}
          icon={<Repeat className="w-5 h-5 text-cyan-600" />}
          description="Live subscriptions generating revenue"
          loading={loading}
          onClick={() => navigate('/p3/finance/subscriptions')}
        />
        <StatCard
          title="Active Customers"
          value={String(kpis?.active_customers?.value || 0)}
          change={kpis?.active_customers?.change_pct}
          trend={Number(kpis?.active_customers?.change_pct || 0) >= 0 ? 'up' : 'down'}
          icon={<Users className="w-5 h-5 text-violet-600" />}
          description="Distinct paying accounts"
          loading={loading}
        />
        <StatCard
          title="Overdue Invoices"
          value={`₹${kpis?.overdue_amount?.value || '0.00'}`}
          change={kpis?.overdue_amount?.change_pct}
          trend={Number(kpis?.overdue_amount?.change_pct || 0) <= 0 ? 'up' : 'down'}
          icon={<AlertTriangle className="w-5 h-5 text-amber-600" />}
          description={`${kpis?.overdue_count?.value || 0} invoices past due date`}
          loading={loading}
          onClick={() => navigate('/p3/finance/invoices?aging=overdue')}
        />
        <StatCard
          title="Customer Churn Rate"
          value={`${kpis?.customer_churn_rate_pct?.value || '0.00'}%`}
          change={kpis?.customer_churn_rate_pct?.change_pct}
          trend={Number(kpis?.customer_churn_rate_pct?.change_pct || 0) <= 0 ? 'up' : 'down'}
          icon={<Percent className="w-5 h-5 text-rose-600" />}
          description="Lost customers / active starting customers"
          loading={loading}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MRR Trajectory Chart */}
        <Card className="p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">MRR Evolution & Growth</h3>
              <p className="text-xs text-slate-500">Monthly recurring revenue trajectory</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/p3/finance/revenue')}>
              View Trend <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mrrTrend}>
                <defs>
                  <linearGradient id="colorMrr" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `₹${v / 1000}k`} />
                <Tooltip formatter={(value: any) => [`₹${Number(value).toLocaleString()}`, 'MRR']} />
                <Area type="monotone" dataKey="mrr" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorMrr)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Invoiced vs Collected Revenue */}
        <Card className="p-5 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Invoiced vs Collected Revenue</h3>
              <p className="text-xs text-slate-500">Cash collection effectiveness</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => navigate('/p3/finance/collections')}>
              Funnel Details <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={revPerf}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="period" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(v) => `₹${v / 1000}k`} />
                <Tooltip formatter={(value: any, name: any) => [`₹${Number(value).toLocaleString()}`, name === 'invoiced' ? 'Total Invoiced' : 'Cash Collected']} />
                <Bar dataKey="invoiced" fill="#94a3b8" radius={[4, 4, 0, 0]} name="invoiced" />
                <Bar dataKey="collected" fill="#10b981" radius={[4, 4, 0, 0]} name="collected" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card
          className="p-4 hover:border-indigo-400 cursor-pointer transition-colors"
          onClick={() => navigate('/p3/finance/revenue')}
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 dark:bg-indigo-950/40 rounded-xl text-indigo-600">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white text-sm">Revenue Analytics</h4>
              <p className="text-xs text-slate-500">MRR waterfall, trend, and forecasting</p>
            </div>
          </div>
        </Card>

        <Card
          className="p-4 hover:border-cyan-400 cursor-pointer transition-colors"
          onClick={() => navigate('/p3/finance/subscriptions')}
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-50 dark:bg-cyan-950/40 rounded-xl text-cyan-600">
              <Repeat className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white text-sm">Subscription Analytics</h4>
              <p className="text-xs text-slate-500">Tier distributions and cohort heatmaps</p>
            </div>
          </div>
        </Card>

        <Card
          className="p-4 hover:border-purple-400 cursor-pointer transition-colors"
          onClick={() => navigate('/p3/finance/collections')}
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-50 dark:bg-purple-950/40 rounded-xl text-purple-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white text-sm">Collection & Risk</h4>
              <p className="text-xs text-slate-500">Aging buckets and collection funnels</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
