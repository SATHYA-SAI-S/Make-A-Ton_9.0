import React, { useEffect, useState } from 'react';
import { CreditCard, CheckCircle2, Clock, ShieldCheck, ArrowDownRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Table, Badge, Button, useToast } from '@/shared/ui';
import { portalApi } from '../../api/portalApi';
import { Payment } from '../../types/portal';

export const PaymentHistory: React.FC = () => {
  const { toast } = useToast();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [balance, setBalance] = useState<string>('0.00');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([portalApi.getPayments(), portalApi.getBalance()])
      .then(([payList, bal]) => {
        setPayments(payList);
        setBalance(bal.outstanding_balance);
      })
      .catch((err) => toast.error('Failed to load payments', err.message))
      .finally(() => setIsLoading(false));
  }, []);

  const columns = [
    {
      key: 'payment_date',
      header: 'Payment Date',
      render: (p: Payment) => <span className="font-medium">{p.payment_date}</span>,
    },
    {
      key: 'reference',
      header: 'Transaction Reference',
      render: (p: Payment) => (
        <span className="font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
          {p.reference}
        </span>
      ),
    },
    {
      key: 'method',
      header: 'Payment Method',
      render: (p: Payment) => (
        <Badge variant="brand" size="sm">
          {p.method}
        </Badge>
      ),
    },
    {
      key: 'amount',
      header: 'Amount Paid',
      align: 'right' as const,
      render: (p: Payment) => (
        <span className="font-bold text-emerald-600 dark:text-emerald-400">
          +₹{Number(p.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      align: 'center' as const,
      render: (p: Payment) => (
        <Badge
          variant={p.status === 'RECORDED' ? 'success' : 'danger'}
          size="sm"
          dot
        >
          {p.status}
        </Badge>
      ),
    },
    {
      key: 'notes',
      header: 'Settlement Notes',
      render: (p: Payment) => (
        <span className="text-xs text-slate-500">{p.notes || 'Automated bank clearing'}</span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Ledger Balance Header */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-emerald-950 via-slate-900 to-slate-900 text-white border border-slate-800 shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" /> Account Settlement Status
          </span>
          <h2 className="text-xl font-bold mt-1">Payments & Credits Ledger</h2>
          <p className="text-xs text-slate-400">
            All bank transfers, UPI transactions, and reconciled allocations.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 text-right">
          <span className="text-[11px] uppercase font-semibold text-slate-300 block">
            Current Outstanding Balance
          </span>
          <span className="text-2xl font-black text-white">
            ₹{Number(balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      <Table
        columns={columns}
        data={payments}
        isLoading={isLoading}
        emptyMessage="No payment records found."
      />
    </div>
  );
};
