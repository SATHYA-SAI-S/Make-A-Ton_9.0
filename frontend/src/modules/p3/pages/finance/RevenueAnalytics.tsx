import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  TrendingUp,
  Download,
  Calendar,
  DollarSign,
  ArrowRight,
  Layers,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area
} from 'recharts';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { FilterBar, AnalyticsFilters } from '../../charts/FilterBar';
import { financeApi } from '../../api/financeApi';
import { RevenuePerformancePoint, MrrTrendPoint, MrrWaterfallData } from '../../types/finance';

export const RevenueAnalytics: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

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
  const [revPerf, setRevPerf] = useState<RevenuePerformancePoint[]>([]);
  const [mrrTrend, setMrrTrend] = useState<MrrTrendPoint[]>([]);
  const [waterfall, setWaterfall] = useState<MrrWaterfallData | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [perfData, trendData, waterfallData] = await Promise.all([
        financeApi.getRevenuePerformance({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
        }),
        financeApi.getMrrTrend({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
          plan_id: filters.planId !== 'ALL' ? filters.planId : undefined,
        }),
        financeApi.getMrrWaterfall({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
        }),
      ]);
      setRevPerf(perfData);
      setMrrTrend(trendData);
      setWaterfall(waterfallData);
    } catch (err) {
      console.error('Error fetching revenue analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Revenue & MRR Analytics
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Comprehensive analysis of billing performance, collection rates, and MRR movements
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
            Export Revenue CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('mrr-trend', { start_date: filters.dateRange.startDate, end_date: filters.dateRange.endDate }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export MRR CSV
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        onChange={(newFilters) => setFilters(newFilters)}
      />

      {/* Chart 1: Invoiced vs Collected Performance */}
      <Card className="p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-indigo-600" />
              Invoiced vs Collected Revenue Over Time
            </h3>
            <p className="text-xs text-slate-500">
              Bar chart of billed vs received cash with collection rate % line
            </p>
          </div>
          <Badge variant="info">Chart 1: /revenue-performance</Badge>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={revPerf}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="period" stroke="#94a3b8" />
              <YAxis yAxisId="left" stroke="#94a3b8" tickFormatter={(v) => `₹${v / 1000}k`} />
              <YAxis yAxisId="right" orientation="right" stroke="#10b981" tickFormatter={(v) => `${v}%`} />
              <Tooltip
                formatter={(val: any, name: any) => {
                  if (name === 'collection_rate_pct') return [`${val}%`, 'Collection Rate'];
                  return [`₹${Number(val).toLocaleString()}`, name === 'invoiced' ? 'Invoiced' : 'Collected'];
                }}
              />
              <Legend />
              <Bar yAxisId="left" dataKey="invoiced" name="Invoiced Revenue" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="left" dataKey="collected" name="Collected Revenue" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="collection_rate_pct" name="Collection Rate %" stroke="#10b981" strokeWidth={2.5} dot={{ r: 4 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Drilldown Table Summary */}
        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-wrap gap-2">
          {revPerf.map((point) => (
            <button
              key={point.period}
              onClick={() => navigate(point.drilldown.url)}
              className="text-xs px-2.5 py-1.5 bg-slate-50 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 text-slate-700 dark:text-slate-300 transition-colors"
            >
              <span className="font-semibold">{point.period}:</span>
              <span>₹{Number(point.collected).toLocaleString()}</span>
              <ArrowRight className="w-3 h-3 text-slate-400" />
            </button>
          ))}
        </div>
      </Card>

      {/* Chart 5: MRR & ARR Trend */}
      <Card className="p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              MRR Evolution & 3-Month Rolling Average
            </h3>
            <p className="text-xs text-slate-500">
              Normalized monthly recurring revenue with moving baseline smoothing
            </p>
          </div>
          <Badge variant="success">Chart 5: /mrr-trend</Badge>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={mrrTrend}>
              <defs>
                <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="period" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" tickFormatter={(v) => `₹${v / 1000}k`} />
              <Tooltip formatter={(val: any, name: any) => [`₹${Number(val).toLocaleString()}`, name]} />
              <Legend />
              <Area type="monotone" dataKey="mrr" name="Monthly Recurring Revenue" stroke="#10b981" strokeWidth={2} fill="url(#trendGradient)" />
              <Line type="monotone" dataKey="rolling_avg_3m" name="3-Month Rolling Avg" stroke="#6366f1" strokeWidth={2} strokeDasharray="4 4" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Chart 6: MRR Movement Waterfall */}
      {waterfall && (
        <Card className="p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-purple-600" />
                MRR Movement Waterfall
              </h3>
              <p className="text-xs text-slate-500">
                Starting MRR + New + Expansion - Contraction - Churn = Ending MRR
              </p>
            </div>
            <Badge variant="default">Chart 6: /mrr-waterfall</Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 mb-6">
            <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
              <span className="text-xs text-slate-500 font-medium">Starting MRR</span>
              <p className="text-base font-bold text-slate-900 dark:text-white">₹{Number(waterfall.starting_mrr).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-200 dark:border-emerald-800">
              <span className="text-xs text-emerald-600 font-medium flex items-center gap-1">
                <ArrowUpRight className="w-3.5 h-3.5" /> New MRR
              </span>
              <p className="text-base font-bold text-emerald-700 dark:text-emerald-400">+₹{Number(waterfall.new_mrr).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-indigo-50 dark:bg-indigo-950/30 rounded-xl border border-indigo-200 dark:border-indigo-800">
              <span className="text-xs text-indigo-600 font-medium flex items-center gap-1">
                <ArrowUpRight className="w-3.5 h-3.5" /> Expansion
              </span>
              <p className="text-base font-bold text-indigo-700 dark:text-indigo-400">+₹{Number(waterfall.expansion_mrr).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-800">
              <span className="text-xs text-amber-600 font-medium flex items-center gap-1">
                <ArrowDownRight className="w-3.5 h-3.5" /> Contraction
              </span>
              <p className="text-base font-bold text-amber-700 dark:text-amber-400">-₹{Number(waterfall.contraction_mrr).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-rose-50 dark:bg-rose-950/30 rounded-xl border border-rose-200 dark:border-rose-800">
              <span className="text-xs text-rose-600 font-medium flex items-center gap-1">
                <ArrowDownRight className="w-3.5 h-3.5" /> Churn
              </span>
              <p className="text-base font-bold text-rose-700 dark:text-rose-400">-₹{Number(waterfall.churn_mrr).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-slate-900 text-white rounded-xl border border-slate-900 shadow-sm">
              <span className="text-xs text-slate-300 font-medium">Ending MRR</span>
              <p className="text-base font-bold text-white">₹{Number(waterfall.ending_mrr).toLocaleString()}</p>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={waterfall.steps}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="category" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" tickFormatter={(v) => `₹${v / 1000}k`} />
                <Tooltip formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Amount']} />
                <Bar
                  dataKey="value"
                  fill="#4f46e5"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
};
