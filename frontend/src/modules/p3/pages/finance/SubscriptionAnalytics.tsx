import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Repeat,
  Download,
  PieChart as PieIcon,
  BarChart2,
  Users,
  Grid,
  ArrowRight,
  TrendingUp
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { FilterBar, AnalyticsFilters } from '../../charts/FilterBar';
import { financeApi } from '../../api/financeApi';
import {
  SubscriptionDistributionData,
  SubscriptionGrowthPoint,
  CohortsData
} from '../../types/finance';

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

export const SubscriptionAnalytics: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [filters, setFilters] = useState<AnalyticsFilters>({
    dateRange: {
      startDate: searchParams.get('start_date') || new Date(Date.now() - 180 * 86400000).toISOString().split('T')[0],
      endDate: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
    },
    frequency: searchParams.get('frequency') || 'ALL',
    planId: searchParams.get('plan_id') || 'ALL',
    status: searchParams.get('status') || 'ALL',
  });

  const [loading, setLoading] = useState(true);
  const [dist, setDist] = useState<SubscriptionDistributionData | null>(null);
  const [growth, setGrowth] = useState<SubscriptionGrowthPoint[]>([]);
  const [cohorts, setCohorts] = useState<CohortsData | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [distData, growthData, cohortData] = await Promise.all([
        financeApi.getSubscriptionDistribution({ as_of: filters.dateRange.endDate }),
        financeApi.getSubscriptionGrowth({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
        }),
        financeApi.getCohorts(6),
      ]);
      setDist(distData);
      setGrowth(growthData);
      setCohorts(cohortData);
    } catch (err) {
      console.error('Error fetching subscription analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Repeat className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Subscription & Cohort Analytics
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Billing frequency breakdown, tier contributions, subscriber movements, and retention matrices
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('subscription-distribution', { end_date: filters.dateRange.endDate }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export Distribution CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('subscription-growth', { start_date: filters.dateRange.startDate, end_date: filters.dateRange.endDate }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export Growth CSV
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar filters={filters} onChange={setFilters} />

      {/* Grid: Distribution by Frequency & Plan */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 2a: Distribution by Billing Frequency */}
        <Card className="p-6 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <PieIcon className="w-5 h-5 text-indigo-600" />
                Distribution by Frequency
              </h3>
              <p className="text-xs text-slate-500">Active subscriptions by billing cycle</p>
            </div>
            <Badge variant="info">Chart 2: /subscription-distribution</Badge>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={dist?.by_frequency || []}
                  dataKey="count"
                  nameKey="frequency"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  innerRadius={45}
                  paddingAngle={3}
                  label={({ frequency, percentage_subs }) => `${frequency} (${percentage_subs}%)`}
                >
                  {(dist?.by_frequency || []).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: any, name: any, item: any) => [`${value} subscriptions (₹${item.payload.mrr} MRR)`, name]} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-2">
            {(dist?.by_frequency || []).map((item, idx) => (
              <div
                key={item.frequency}
                onClick={() => navigate(item.drilldown.url)}
                className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 cursor-pointer border border-slate-200 dark:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{item.frequency}</span>
                </div>
                <p className="text-sm font-bold text-slate-900 dark:text-white">{item.count}</p>
                <p className="text-xs text-slate-500">₹{Number(item.mrr).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Chart 2b: Distribution by Plan Tier */}
        <Card className="p-6 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-emerald-600" />
                Distribution by Plan Tier
              </h3>
              <p className="text-xs text-slate-500">MRR contribution per subscription plan</p>
            </div>
            <Badge variant="success">Tier Breakdown</Badge>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dist?.by_plan || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" stroke="#94a3b8" tickFormatter={(v) => `₹${v / 1000}k`} />
                <YAxis dataKey="plan_name" type="category" width={110} stroke="#94a3b8" fontSize={11} />
                <Tooltip formatter={(value: any) => [`₹${Number(value).toLocaleString()}`, 'MRR']} />
                <Bar dataKey="mrr" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap gap-2">
            {(dist?.by_plan || []).map((p) => (
              <button
                key={p.plan_id}
                onClick={() => navigate(p.drilldown.url)}
                className="text-xs px-2.5 py-1 bg-slate-50 dark:bg-slate-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1.5"
              >
                <span>{p.plan_name}:</span>
                <span className="font-semibold">{p.count} subs ({p.percentage_mrr}%)</span>
              </button>
            ))}
          </div>
        </Card>
      </div>

      {/* Chart 4: Subscription Growth Movements */}
      <Card className="p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              Subscription Growth: New, Renewed, and Closed
            </h3>
            <p className="text-xs text-slate-500">
              Stacked bar chart of monthly additions, renewals, and cancellations
            </p>
          </div>
          <Badge variant="default">Chart 4: /subscription-growth</Badge>
        </div>

        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={growth}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="period" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Legend />
              <Bar dataKey="new" name="New Subscriptions" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="renewed" name="Renewals" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              <Bar dataKey="closed" name="Cancellations / Closed" fill="#f43f5e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Chart 7: Customer Cohort Retention Heatmap */}
      {cohorts && (
        <Card className="p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Grid className="w-5 h-5 text-purple-600" />
                Monthly Customer Cohort Retention Matrix
              </h3>
              <p className="text-xs text-slate-500">
                Retention percentage by customer acquisition month over time (Month 0 to Month 5)
              </p>
            </div>
            <Badge variant="default">Chart 7: /cohorts</Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="py-2.5 px-3">Cohort</th>
                  <th className="py-2.5 px-3">Size</th>
                  {cohorts.intervals.map((inv) => (
                    <th key={inv} className="py-2.5 px-3 text-center">{inv}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {cohorts.cohorts.map((row) => (
                  <tr key={row.cohort} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-semibold text-slate-900 dark:text-white">
                      <button
                        onClick={() => navigate(row.drilldown.url)}
                        className="text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                      >
                        {row.cohort}
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-xs">{row.cohort_size} customers</td>
                    {row.retention.map((rate, i) => {
                      if (rate === null) {
                        return <td key={i} className="py-2.5 px-3 text-center text-slate-300">-</td>;
                      }
                      // Color scale based on retention rate
                      const bg = rate >= 80 ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300' :
                        rate >= 60 ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300' :
                          'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300';
                      return (
                        <td key={i} className="py-2 px-2 text-center">
                          <span className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold ${bg}`}>
                            {rate}%
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
