import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Download,
  Users,
  X,
  ArrowRight,
  TrendingUp,
  Percent,
  CheckCircle,
  Clock
} from 'lucide-react';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Modal } from '@/shared/ui/Modal';
import { Table, Column } from '@/shared/ui/Table';
import { financeApi } from '../../api/financeApi';
import { CohortsData } from '../../types/finance';

interface CellCustomer {
  customer_id: string;
  name: string;
  email: string;
  status: string;
  current_plan: string;
  current_mrr: string;
}

export const CohortRetentionPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [cohortData, setCohortData] = useState<CohortsData | null>(null);
  const [lookback, setLookback] = useState(12);

  // Cell drilldown state
  const [selectedCell, setSelectedCell] = useState<{ cohort: string; offset: number } | null>(null);
  const [cellLoading, setCellLoading] = useState(false);
  const [cellCustomers, setCellCustomers] = useState<CellCustomer[]>([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await financeApi.getCohorts(lookback);
      setCohortData(data);
    } catch (err) {
      console.error('Failed to load cohort retention:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [lookback]);

  const handleCellClick = async (cohort: string, offset: number, rate: number | null) => {
    if (rate === null) return;
    setSelectedCell({ cohort, offset });
    setCellLoading(true);
    try {
      const token = localStorage.getItem('token') || 'dev-admin-token';
      const res = await fetch(`/api/v1/finance/charts/cohorts/cell-customers?cohort=${cohort}&offset=${offset}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const d = await res.json();
        setCellCustomers(d.customers || []);
      }
    } catch (e) {
      console.error('Failed to load cell customers:', e);
    } finally {
      setCellLoading(false);
    }
  };

  const customerColumns: Column<CellCustomer>[] = [
    {
      key: 'name',
      header: 'Customer',
      render: (c) => (
        <div>
          <span className="font-semibold text-slate-900 dark:text-white block">{c.name}</span>
          <span className="text-xs text-slate-400">{c.email}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (c) => (
        <Badge variant={c.status === 'ACTIVE' ? 'success' : 'default'}>
          {c.status}
        </Badge>
      ),
    },
    {
      key: 'current_plan',
      header: 'Plan Tier',
      render: (c) => <span className="text-xs font-medium">{c.current_plan}</span>,
    },
    {
      key: 'current_mrr',
      header: 'Current MRR',
      align: 'right',
      render: (c) => <span className="font-mono font-bold text-emerald-600">₹{Number(c.current_mrr).toLocaleString()}</span>,
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Grid className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            Customer Cohort Retention Heatmap
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Triangular retention matrix by customer acquisition month. Click any cell to view active customer accounts.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={lookback}
            onChange={(e) => setLookback(Number(e.target.value))}
            className="text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 py-1.5 px-3"
          >
            <option value={6}>Past 6 Months</option>
            <option value={12}>Past 12 Months</option>
            <option value={24}>Past 24 Months</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(financeApi.getExportUrl('subscription-growth'), '_blank')}
            className="flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Cohort Matrix Table */}
      <Card className="p-6 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4">Cohort Month</th>
                <th className="py-3 px-4">Acquired</th>
                {cohortData?.intervals.map((inv) => (
                  <th key={inv} className="py-3 px-3 text-center">{inv}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {cohortData?.cohorts.map((row) => (
                <tr key={row.cohort} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20">
                  <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                    {row.cohort}
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-600 dark:text-slate-300">
                    {row.cohort_size} accounts
                  </td>
                  {row.retention.map((rate, idx) => {
                    if (rate === null) {
                      return (
                        <td key={idx} className="py-2 px-2 text-center text-slate-300 dark:text-slate-700">
                          -
                        </td>
                      );
                    }

                    // Heatmap color intensity
                    const cellColor =
                      rate >= 90
                        ? 'bg-emerald-500 text-white'
                        : rate >= 80
                          ? 'bg-emerald-400 text-white'
                          : rate >= 70
                            ? 'bg-indigo-400 text-white'
                            : rate >= 50
                              ? 'bg-indigo-300 text-slate-900'
                              : rate >= 30
                                ? 'bg-amber-300 text-slate-900'
                                : 'bg-rose-300 text-slate-900';

                    return (
                      <td key={idx} className="p-1.5 text-center">
                        <button
                          onClick={() => handleCellClick(row.cohort, idx, rate)}
                          className={`w-full py-2 px-1 rounded-lg text-xs font-bold transition-transform hover:scale-105 shadow-sm ${cellColor}`}
                          title={`Click to view ${row.cohort} Month ${idx} customers`}
                        >
                          {rate}%
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Drill-down Modal for Selected Cell */}
      {selectedCell && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedCell(null)}
          title={`Cohort ${selectedCell.cohort} — Month ${selectedCell.offset} Accounts (${cellCustomers.length})`}
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-500">
              Customers who originally acquired their first subscription in {selectedCell.cohort} and remained active or paused in Month {selectedCell.offset}.
            </p>
            <Table
              columns={customerColumns}
              data={cellCustomers}
              keyExtractor={(c) => c.customer_id}
              loading={cellLoading}
              emptyText="No customers found in this cell."
            />
          </div>
        </Modal>
      )}
    </div>
  );
};
