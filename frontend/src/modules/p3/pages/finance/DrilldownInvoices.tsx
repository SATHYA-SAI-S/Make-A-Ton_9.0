import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Download,
  ArrowLeft,
  ExternalLink,
  Filter,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Table, Column } from '@/shared/ui/Table';
import { financeApi } from '../../api/financeApi';

interface DrilldownInvoice {
  id: string;
  number: string;
  customer_id: string;
  subscription_id?: string;
  status: string;
  invoice_date: string;
  due_date: string;
  total: string;
  amount_paid: string;
  balance: string;
}

export const DrilldownInvoices: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const aging = searchParams.get('aging');
  const period = searchParams.get('period');
  const customerId = searchParams.get('customer_id');

  const [loading, setLoading] = useState(true);
  const [invoices, setInvoices] = useState<DrilldownInvoice[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);

  const loadInvoices = async () => {
    setLoading(true);
    try {
      // Fetch invoices matching filters via portal API or finance endpoint
      const res = await fetch(`/api/v1/portal/invoices?page=${page}&page_size=20${aging ? `&aging=${aging}` : ''}${period ? `&period=${period}` : ''}${customerId ? `&customer_id=${customerId}` : ''}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'dev-admin-token'}`,
        }
      });
      if (res.ok) {
        const data = await res.json();
        setInvoices(data.items || []);
        setTotalCount(data.total || (data.items || []).length);
      } else {
        // Fallback for mocked view
        setInvoices([]);
      }
    } catch (err) {
      console.error('Failed to load drilldown invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, [searchParams, page]);

  const columns: Column<DrilldownInvoice>[] = [
    {
      key: 'number',
      header: 'Invoice #',
      render: (inv) => (
        <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
          {inv.number}
        </span>
      ),
    },
    {
      key: 'customer_id',
      header: 'Customer ID',
      render: (inv) => <span className="font-mono text-xs">{inv.customer_id}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (inv) => (
        <Badge
          variant={
            inv.status === 'PAID'
              ? 'success'
              : inv.status === 'PARTIALLY_PAID'
                ? 'warning'
                : inv.status === 'CANCELLED'
                  ? 'danger'
                  : 'default'
          }
        >
          {inv.status}
        </Badge>
      ),
    },
    {
      key: 'invoice_date',
      header: 'Invoice Date',
      render: (inv) => <span className="text-xs text-slate-500">{inv.invoice_date}</span>,
    },
    {
      key: 'due_date',
      header: 'Due Date',
      render: (inv) => <span className="text-xs text-slate-500">{inv.due_date}</span>,
    },
    {
      key: 'total',
      header: 'Total',
      align: 'right',
      render: (inv) => <span className="font-mono font-semibold">₹{Number(inv.total).toLocaleString()}</span>,
    },
    {
      key: 'balance',
      header: 'Balance Due',
      align: 'right',
      render: (inv) => (
        <span className={`font-mono font-bold ${Number(inv.balance) > 0 ? 'text-amber-600' : 'text-slate-400'}`}>
          ₹{Number(inv.balance).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Contracts Link',
      align: 'right',
      render: (inv) => (
        <div className="flex items-center justify-end gap-2">
          {inv.subscription_id && (
            <a
              href={`/subscriptions/${inv.subscription_id}`}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-indigo-600 hover:underline flex items-center gap-1"
              title="Person 1 Subscription Page"
            >
              Sub <ExternalLink className="w-3 h-3" />
            </a>
          )}
          <a
            href={`/invoices/${inv.id}`}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-slate-600 hover:underline flex items-center gap-1"
            title="Person 2 Invoice Page"
          >
            Inv <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 mb-1"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Analytics
          </button>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-indigo-600" />
            Drilldown Invoices
          </h1>
          <p className="text-sm text-slate-500">
            {aging && `Filtered by aging interval: ${aging}`}
            {period && `Filtered by period: ${period}`}
            {customerId && ` • Customer: ${customerId}`}
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open(financeApi.getExportUrl('invoices', { aging, period, customer_id: customerId }), '_blank')}
          className="flex items-center gap-1.5"
        >
          <Download className="w-4 h-4" />
          Export Invoices CSV
        </Button>
      </div>

      <Card className="p-4 shadow-sm">
        <Table
          columns={columns}
          data={invoices}
          keyExtractor={(inv) => inv.id}
          loading={loading}
          emptyText="No invoices found matching active filter criteria."
        />
      </Card>
    </div>
  );
};
