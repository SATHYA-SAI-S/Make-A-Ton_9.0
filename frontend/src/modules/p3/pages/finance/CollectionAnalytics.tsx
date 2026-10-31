import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  Download,
  Filter,
  DollarSign,
  ArrowRight,
  TrendingDown,
  Users,
  ShieldAlert,
  CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { FilterBar, AnalyticsFilters } from '../../charts/FilterBar';
import { financeApi } from '../../api/financeApi';
import {
  InvoiceAgingData,
  CollectionFunnelData,
  RevenueConcentrationData
} from '../../types/finance';

const RISK_COLORS: Record<string, string> = {
  LOW: '#10b981',      // Green (Current)
  MODERATE: '#f59e0b', // Amber (1-30)
  HIGH: '#f97316',     // Orange (31-60)
  SEVERE: '#ef4444',   // Red (61-90)
  CRITICAL: '#b91c1c', // Dark Red (90+)
};

export const CollectionAnalytics: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [filters, setFilters] = useState<AnalyticsFilters>({
    dateRange: {
      startDate: searchParams.get('start_date') || new Date(Date.now() - 90 * 86400000).toISOString().split('T')[0],
      endDate: searchParams.get('end_date') || new Date().toISOString().split('T')[0],
    },
    frequency: searchParams.get('frequency') || 'ALL',
    planId: searchParams.get('plan_id') || 'ALL',
    status: searchParams.get('status') || 'ALL',
  });

  const [loading, setLoading] = useState(true);
  const [aging, setAging] = useState<InvoiceAgingData | null>(null);
  const [funnel, setFunnel] = useState<CollectionFunnelData | null>(null);
  const [concentration, setConcentration] = useState<RevenueConcentrationData | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [agingData, funnelData, concData] = await Promise.all([
        financeApi.getInvoiceAging({ as_of: filters.dateRange.endDate }),
        financeApi.getCollectionFunnel({
          start_date: filters.dateRange.startDate,
          end_date: filters.dateRange.endDate,
        }),
        financeApi.getRevenueConcentration(10),
      ]);
      setAging(agingData);
      setFunnel(funnelData);
      setConcentration(concData);
    } catch (err) {
      console.error('Error fetching collection analytics:', err);
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
            <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            Collection, Aging & Risk Analytics
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Invoice aging intervals, payment conversion funnels, and customer concentration risk
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('invoice-aging', { end_date: filters.dateRange.endDate }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export Aging CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('collection-funnel', { start_date: filters.dateRange.startDate, end_date: filters.dateRange.endDate }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export Funnel CSV
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar filters={filters} onChange={setFilters} />

      {/* Chart 3: Invoice Aging Buckets */}
      <Card className="p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-600" />
              Invoice Aging Buckets & Overdue Balances
            </h3>
            <p className="text-xs text-slate-500">
              Total outstanding balances grouped by days past due date (as of {aging?.as_of_date})
            </p>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-500 font-medium">Total Unpaid Balance</span>
            <p className="text-lg font-bold text-slate-900 dark:text-white">₹{Number(aging?.total_outstanding || 0).toLocaleString()}</p>
          </div>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={aging?.buckets || []}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="label" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" tickFormatter={(v) => `₹${v / 1000}k`} />
              <Tooltip formatter={(value: any) => [`₹${Number(value).toLocaleString()}`, 'Outstanding Balance']} />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {(aging?.buckets || []).map((b) => (
                  <Cell key={b.bucket} fill={RISK_COLORS[b.risk_level] || '#4f46e5'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Drill-down Cards for each Bucket */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
          {(aging?.buckets || []).map((b) => (
            <div
              key={b.bucket}
              onClick={() => navigate(b.drilldown.url)}
              className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:border-indigo-400 border border-slate-200 dark:border-slate-700 cursor-pointer transition-all"
            >
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{b.label}</span>
                <Badge variant={b.risk_level === 'LOW' ? 'success' : b.risk_level === 'CRITICAL' ? 'danger' : 'warning'}>
                  {b.risk_level}
                </Badge>
              </div>
              <p className="text-sm font-bold text-slate-900 dark:text-white">₹{Number(b.amount).toLocaleString()}</p>
              <div className="flex justify-between items-center text-xs text-slate-500 mt-1">
                <span>{b.count} invoices</span>
                <span>{b.percentage}%</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Chart 9: Payment Collection Funnel */}
      {funnel && (
        <Card className="p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-indigo-600" />
                Payment Collection Funnel Conversion
              </h3>
              <p className="text-xs text-slate-500">
                Conversion progress from invoice generation to confirmed, partially paid, and fully settled
              </p>
            </div>
            <Badge variant="info">Chart 9: /collection-funnel</Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            {funnel.stages.map((stage, idx) => (
              <div
                key={stage.stage}
                className="relative p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm"
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Step {idx + 1}</span>
                  <span className="text-xs font-bold text-indigo-600">{stage.conversion_pct}%</span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white">{stage.label}</h4>
                <p className="text-lg font-bold text-slate-900 dark:text-white my-1">₹{Number(stage.amount).toLocaleString()}</p>
                <p className="text-xs text-slate-500">{stage.count} invoices</p>

                {stage.dropoff_pct > 0 && (
                  <div className="mt-2 text-xs font-medium text-rose-600 flex items-center gap-1">
                    <TrendingDown className="w-3.5 h-3.5" />
                    <span>Drop-off: {stage.dropoff_pct}%</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Chart 8: Revenue Pareto Concentration */}
      {concentration && (
        <Card className="p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-600" />
                Top 10 Customer Revenue & Pareto Concentration
              </h3>
              <p className="text-xs text-slate-500">
                Customer account concentration analysis and revenue dependency risk
              </p>
            </div>
            <Badge variant={concentration.pareto_summary.risk_status === 'CONCENTRATED' ? 'warning' : 'success'}>
              {concentration.pareto_summary.risk_status} ({concentration.pareto_summary.top_10_share_pct}%)
            </Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                  <th className="py-2.5 px-3">#</th>
                  <th className="py-2.5 px-3">Customer</th>
                  <th className="py-2.5 px-3 text-right">Annual Invoiced</th>
                  <th className="py-2.5 px-3 text-right">Current MRR</th>
                  <th className="py-2.5 px-3 text-right">Revenue Share</th>
                  <th className="py-2.5 px-3 text-right">Cumulative Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {concentration.top_customers.map((c, idx) => (
                  <tr key={c.customer_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-semibold text-slate-400">{idx + 1}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900 dark:text-white">
                      <button
                        onClick={() => navigate(c.drilldown.url)}
                        className="text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                      >
                        {c.customer_name}
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono">₹{Number(c.annual_invoiced).toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-right font-mono text-emerald-600">₹{Number(c.current_mrr).toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-right font-bold text-slate-700 dark:text-slate-300">{c.share_pct}%</td>
                    <td className="py-2.5 px-3 text-right text-indigo-600 font-semibold">{c.cumulative_share_pct}%</td>
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
