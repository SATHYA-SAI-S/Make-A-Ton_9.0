import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Download,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Percent,
  Layers,
  Building,
  CheckCircle2
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
  Legend
} from 'recharts';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Modal } from '@/shared/ui/Modal';
import { Table, Column } from '@/shared/ui/Table';
import { financeApi } from '../../api/financeApi';
import { RevenueConcentrationData, CustomerShare } from '../../types/finance';

export const RevenueConcentrationPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<RevenueConcentrationData | null>(null);
  const [topN, setTopN] = useState(10);
  const [sortBy, setSortBy] = useState<'mrr' | 'revenue'>('mrr');

  // Selected customer for plan-breakdown modal
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerShare | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const conc = await financeApi.getRevenueConcentration(topN);
      setData(conc);
    } catch (err) {
      console.error('Failed to load revenue concentration:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [topN, sortBy]);

  const paretoSummary = data?.pareto_summary;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            Revenue Concentration & Pareto Dependency
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Evaluating top account dependencies, cumulative revenue shares, and diversification risk
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            className="text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 py-1.5 px-3"
          >
            <option value={5}>Top 5 Customers</option>
            <option value={10}>Top 10 Customers</option>
            <option value={20}>Top 20 Customers</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('concentration', { top_n: topN }), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export Pareto CSV
          </Button>
        </div>
      </div>

      {/* Risk Alert Banner */}
      <Card className="p-5 shadow-sm border-l-4 border-indigo-500 bg-gradient-to-r from-indigo-50/40 to-transparent dark:from-indigo-950/20">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-white dark:bg-slate-800 rounded-xl shadow-xs text-indigo-600">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900 dark:text-white">Pareto Concentration Summary</h3>
                <Badge
                  variant={
                    paretoSummary?.risk_status === 'HEALTHY_DIVERSIFICATION'
                      ? 'success'
                      : paretoSummary?.risk_status === 'CRITICAL_CONCENTRATION'
                        ? 'danger'
                        : 'warning'
                  }
                >
                  {paretoSummary?.risk_status || 'ANALYZING'}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Top {topN} accounts contribute <span className="font-bold text-indigo-600">{paretoSummary?.top_10_share_pct}%</span> of total recurring MRR.
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-400 font-medium">Total Monthly Recurring Revenue</span>
            <p className="text-xl font-bold text-slate-900 dark:text-white font-mono">₹{Number(data?.total_active_mrr || 0).toLocaleString()}</p>
          </div>
        </div>
      </Card>

      {/* Pareto Composed Chart */}
      <Card className="p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
          Pareto Curve: Individual vs Cumulative MRR Share
        </h3>
        <p className="text-xs text-slate-500 mb-6">
          Bars represent individual customer share %; the line represents cumulative dependency %
        </p>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data?.top_customers || []}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="customer_name" stroke="#94a3b8" fontSize={11} interval={0} angle={-15} textAnchor="end" height={50} />
              <YAxis yAxisId="left" stroke="#94a3b8" tickFormatter={(v) => `${v}%`} />
              <YAxis yAxisId="right" orientation="right" stroke="#4f46e5" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip formatter={(val: any, name: any) => [`${val}%`, name === 'share_pct' ? 'Individual Share' : 'Cumulative Share']} />
              <Legend />
              <Bar yAxisId="left" dataKey="share_pct" name="Individual Share %" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="cumulative_share_pct" name="Cumulative Share %" stroke="#4f46e5" strokeWidth={3} dot={{ r: 5 }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Top Customers Detailed Table */}
      <Card className="p-6 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 dark:text-white mb-4">
          Top {topN} Customer Ranking Breakdown
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                <th className="py-3 px-3">#</th>
                <th className="py-3 px-3">Customer Name</th>
                <th className="py-3 px-3 text-right">Annual Invoiced</th>
                <th className="py-3 px-3 text-right">Current MRR</th>
                <th className="py-3 px-3 text-right">MRR Share</th>
                <th className="py-3 px-3 text-right">Cumulative Share</th>
                <th className="py-3 px-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {(data?.top_customers || []).map((c, idx) => (
                <tr key={c.customer_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="py-3 px-3 font-bold text-slate-400">{idx + 1}</td>
                  <td className="py-3 px-3 font-semibold text-slate-900 dark:text-white">
                    {c.customer_name}
                  </td>
                  <td className="py-3 px-3 text-right font-mono">₹{Number(c.annual_invoiced).toLocaleString()}</td>
                  <td className="py-3 px-3 text-right font-mono text-emerald-600 font-bold">₹{Number(c.current_mrr).toLocaleString()}</td>
                  <td className="py-3 px-3 text-right font-bold text-slate-700 dark:text-slate-300">{c.share_pct}%</td>
                  <td className="py-3 px-3 text-right font-semibold text-indigo-600">{c.cumulative_share_pct}%</td>
                  <td className="py-3 px-3 text-center">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedCustomer(c)}
                      className="text-xs py-1 px-2"
                    >
                      Plan Breakdown
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Plan Breakdown Modal */}
      {selectedCustomer && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedCustomer(null)}
          title={`${selectedCustomer.customer_name} — Subscription Plan Breakdown`}
        >
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <div>
                <span className="text-xs text-slate-500">Customer Total MRR</span>
                <p className="text-base font-bold text-emerald-600 font-mono">₹{Number(selectedCustomer.current_mrr).toLocaleString()}</p>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500">Share of Total MRR</span>
                <p className="text-base font-bold text-indigo-600">{selectedCustomer.share_pct}%</p>
              </div>
            </div>

            <p className="text-xs text-slate-500 font-medium">Active Subscription Plans:</p>
            <div className="divide-y divide-slate-100 dark:divide-slate-800 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
              <div className="p-3 bg-white dark:bg-slate-900 flex justify-between items-center">
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white">Active Subscriptions</h4>
                  <p className="text-xs text-slate-400">Recurring billing lines snapshot</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/p3/finance/subscriptions?customer_id=${selectedCustomer.customer_id}`)}
                >
                  View Records <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
