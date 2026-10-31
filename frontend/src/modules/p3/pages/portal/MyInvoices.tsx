import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  AlertCircle,
  CheckCircle2,
  Calendar,
  DollarSign,
  Eye,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Table,
  Badge,
  Button,
  Modal,
  Tabs,
  useToast,
} from '@/shared/ui';
import { portalApi } from '../../api/portalApi';
import { Invoice } from '../../types/portal';

export const MyInvoices: React.FC = () => {
  const { toast } = useToast();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Detail Modal
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const fetchInvoices = () => {
    setIsLoading(true);
    portalApi
      .getInvoices(selectedStatus)
      .then((res) => setInvoices(res))
      .catch((err) => toast.error('Failed to load invoices', err.message))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchInvoices();
  }, [selectedStatus]);

  const handleDownloadPdf = async (inv: Invoice) => {
    try {
      await portalApi.downloadInvoicePdf(inv.id, inv.number);
      toast.success('Downloaded', `Invoice ${inv.number} downloaded.`);
    } catch (err: any) {
      toast.error('Download Failed', err.message);
    }
  };

  const statusTabs = [
    { id: 'ALL', label: 'All Invoices' },
    { id: 'CONFIRMED', label: 'Unpaid / Pending' },
    { id: 'PAID', label: 'Paid' },
  ];

  const columns = [
    {
      key: 'number',
      header: 'Invoice #',
      render: (inv: Invoice) => (
        <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
          {inv.number}
        </span>
      ),
    },
    { key: 'invoice_date', header: 'Invoice Date' },
    {
      key: 'due_date',
      header: 'Due Date',
      render: (inv: Invoice) => (
        <div className="flex items-center gap-1.5">
          <span>{inv.due_date}</span>
          {inv.is_overdue && (
            <Badge variant="danger" size="sm">
              OVERDUE
            </Badge>
          )}
        </div>
      ),
    },
    {
      key: 'total',
      header: 'Total',
      align: 'right' as const,
      render: (inv: Invoice) => (
        <span className="font-bold text-slate-900 dark:text-slate-100">
          ₹{Number(inv.total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: 'balance',
      header: 'Balance Due',
      align: 'right' as const,
      render: (inv: Invoice) => (
        <span
          className={`font-semibold ${
            Number(inv.balance) > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-slate-400'
          }`}
        >
          ₹{Number(inv.balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      align: 'center' as const,
      render: (inv: Invoice) => (
        <Badge
          variant={
            inv.status === 'PAID'
              ? 'success'
              : inv.status === 'CONFIRMED'
              ? 'warning'
              : 'neutral'
          }
          size="sm"
          dot
        >
          {inv.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right' as const,
      render: (inv: Invoice) => (
        <div className="inline-flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedInvoice(inv)}
            leftIcon={<Eye className="w-3.5 h-3.5" />}
          >
            View
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownloadPdf(inv)}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            PDF
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            My Invoices
          </h1>
          <p className="text-xs text-slate-500">
            Official tax invoices, itemized line breakdowns, and payment receipts.
          </p>
        </div>

        <Tabs
          tabs={statusTabs}
          activeTab={selectedStatus}
          onChange={setSelectedStatus}
          variant="pills"
        />
      </div>

      <Table
        columns={columns}
        data={invoices}
        isLoading={isLoading}
        emptyMessage={`No invoices found matching status "${selectedStatus}".`}
      />

      {/* Invoice Detail Dialog Modal */}
      <Modal
        isOpen={Boolean(selectedInvoice)}
        onClose={() => setSelectedInvoice(null)}
        title={`Invoice Breakdown — ${selectedInvoice?.number}`}
        size="lg"
        footer={
          <>
            <Button variant="ghost" onClick={() => setSelectedInvoice(null)}>
              Close
            </Button>
            {selectedInvoice && (
              <Button
                variant="primary"
                onClick={() => handleDownloadPdf(selectedInvoice)}
                leftIcon={<Download className="w-4 h-4" />}
              >
                Download Official PDF
              </Button>
            )}
          </>
        }
      >
        {selectedInvoice && (
          <div className="space-y-5 text-xs">
            {/* Header meta */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <div>
                <span className="text-slate-400 block">Invoice Date</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedInvoice.invoice_date}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Payment Due</span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">{selectedInvoice.due_date}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Status</span>
                <Badge variant={selectedInvoice.status === 'PAID' ? 'success' : 'warning'} size="sm" dot>
                  {selectedInvoice.status}
                </Badge>
              </div>
              <div>
                <span className="text-slate-400 block">Subscription Ref</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">{selectedInvoice.subscription_id}</span>
              </div>
            </div>

            {/* Itemized lines */}
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 uppercase text-[10px] font-bold">
                  <tr>
                    <th className="px-3.5 py-2.5">Line Description</th>
                    <th className="px-3.5 py-2.5 text-center">Qty</th>
                    <th className="px-3.5 py-2.5 text-right">Unit Price</th>
                    <th className="px-3.5 py-2.5 text-right">Tax (18%)</th>
                    <th className="px-3.5 py-2.5 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {selectedInvoice.lines?.map((line) => (
                    <tr key={line.id}>
                      <td className="px-3.5 py-2.5 font-medium text-slate-800 dark:text-slate-200">{line.description}</td>
                      <td className="px-3.5 py-2.5 text-center">{line.quantity}</td>
                      <td className="px-3.5 py-2.5 text-right">₹{Number(line.unit_price).toLocaleString('en-IN')}</td>
                      <td className="px-3.5 py-2.5 text-right">₹{Number(line.tax_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="px-3.5 py-2.5 text-right font-semibold">₹{Number(line.line_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Totals Summary */}
            <div className="flex justify-end">
              <div className="w-64 space-y-1.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                <div className="flex justify-between text-slate-500">
                  <span>Subtotal:</span>
                  <span>₹{Number(selectedInvoice.subtotal).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Tax Total (GST):</span>
                  <span>₹{Number(selectedInvoice.tax_total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between font-bold text-sm text-slate-900 dark:text-slate-100 pt-1 border-t border-slate-200 dark:border-slate-700">
                  <span>Grand Total:</span>
                  <span>₹{Number(selectedInvoice.total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between font-semibold text-emerald-600 pt-0.5">
                  <span>Amount Paid:</span>
                  <span>₹{Number(selectedInvoice.amount_paid).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between font-bold text-amber-600 pt-0.5">
                  <span>Remaining Balance:</span>
                  <span>₹{Number(selectedInvoice.balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
