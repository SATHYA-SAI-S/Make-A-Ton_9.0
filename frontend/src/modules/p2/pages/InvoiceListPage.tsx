import React, { useEffect, useState } from 'react';
import { invoiceApi } from '../api';
import { Invoice, InvoiceStatus } from '../types';
import { Card, Badge, Modal, StatCard } from '../components';

export const InvoiceListPage: React.FC<{
  onSelectInvoice?: (invoiceId: string) => void;
}> = ({ onSelectInvoice }) => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Cancel modal state
  const [cancellingInv, setCancellingInv] = useState<Invoice | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const res = await invoiceApi.getInvoices({ status: statusFilter || undefined });
      setInvoices(res.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInvoices();
  }, [statusFilter]);

  const handleConfirm = async (id: string) => {
    if (!window.confirm('Are you sure you want to confirm this draft invoice?')) return;
    try {
      await invoiceApi.confirmInvoice(id);
      await loadInvoices();
    } catch (err: any) {
      alert(`Failed to confirm invoice: ${err.message}`);
    }
  };

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancellingInv) return;
    try {
      await invoiceApi.cancelInvoice(cancellingInv.id, cancelReason);
      setCancellingInv(null);
      setCancelReason('');
      await loadInvoices();
    } catch (err: any) {
      alert(`Failed to cancel invoice: ${err.message}`);
    }
  };

  const downloadPdf = async (inv: Invoice) => {
    try {
      const blob = await invoiceApi.getPdf(inv.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${inv.number}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Failed to download PDF: ${err.message}`);
    }
  };

  // Metrics
  const totalInvoiced = invoices.reduce((acc, inv) => acc + parseFloat(inv.total || '0'), 0);
  const totalCollected = invoices.reduce((acc, inv) => acc + parseFloat(inv.amount_paid || '0'), 0);
  const totalOutstanding = invoices.reduce((acc, inv) => acc + parseFloat(inv.balance || '0'), 0);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#111827' }}>Invoices Management</h1>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            Lifecycle tracking, immutable snapshots, ReportLab PDF rendering, and printable templates
          </p>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Metrics Row */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <StatCard title="Total Invoiced" value={`₹${totalInvoiced.toFixed(2)}`} subtitle={`${invoices.length} total invoices`} />
        <StatCard title="Total Collected" value={`₹${totalCollected.toFixed(2)}`} subtitle="Paid across invoices" variant="success" />
        <StatCard title="Outstanding Balance" value={`₹${totalOutstanding.toFixed(2)}`} subtitle="Pending collection" variant="warning" />
      </div>

      {/* Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px', color: '#4B5563', fontWeight: 600 }}>Filter Status:</span>
          {['', 'DRAFT', 'CONFIRMED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
                border: '1px solid #D1D5DB',
                backgroundColor: statusFilter === st ? '#1E40AF' : '#FFFFFF',
                color: statusFilter === st ? '#FFFFFF' : '#374151',
                cursor: 'pointer'
              }}
            >
              {st || 'ALL'}
            </button>
          ))}
        </div>
      </div>

      {/* Invoices Table */}
      <Card>
        {loading ? (
          <div>Loading invoices...</div>
        ) : invoices.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#6B7280' }}>No invoices found matching current filter.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
                <th style={{ padding: '10px 12px' }}>Invoice #</th>
                <th style={{ padding: '10px 12px' }}>Date</th>
                <th style={{ padding: '10px 12px' }}>Due Date</th>
                <th style={{ padding: '10px 12px' }}>Total</th>
                <th style={{ padding: '10px 12px' }}>Paid</th>
                <th style={{ padding: '10px 12px' }}>Balance</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} style={{ borderBottom: '1px solid #F3F4F6', fontSize: '14px' }}>
                  <td style={{ padding: '12px', fontWeight: 700, fontFamily: 'monospace', color: '#1E40AF' }}>
                    <a
                      href={`#invoice-${inv.id}`}
                      onClick={(e) => {
                        e.preventDefault();
                        if (onSelectInvoice) onSelectInvoice(inv.id);
                      }}
                      style={{ color: '#1D4ED8', textDecoration: 'none' }}
                    >
                      {inv.number}
                    </a>
                  </td>
                  <td style={{ padding: '12px', color: '#4B5563' }}>{inv.invoice_date}</td>
                  <td style={{ padding: '12px', color: '#4B5563' }}>{inv.due_date}</td>
                  <td style={{ padding: '12px', fontWeight: 600 }}>₹{inv.total}</td>
                  <td style={{ padding: '12px', color: '#059669' }}>₹{inv.amount_paid}</td>
                  <td style={{ padding: '12px', fontWeight: 600, color: parseFloat(inv.balance) > 0 ? '#DC2626' : '#4B5563' }}>
                    ₹{inv.balance}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={inv.status} />
                    {inv.is_overdue && <Badge status="OVERDUE" variant="danger" />}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      {inv.status === 'DRAFT' && (
                        <button
                          onClick={() => handleConfirm(inv.id)}
                          style={{
                            padding: '4px 8px',
                            background: '#D1FAE5',
                            color: '#065F46',
                            border: '1px solid #A7F3D0',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                            fontWeight: 600
                          }}
                        >
                          Confirm
                        </button>
                      )}
                      {(inv.status === 'DRAFT' || inv.status === 'CONFIRMED') && parseFloat(inv.amount_paid) === 0 && (
                        <button
                          onClick={() => setCancellingInv(inv)}
                          style={{
                            padding: '4px 8px',
                            background: '#FEE2E2',
                            color: '#991B1B',
                            border: '1px solid #FECACA',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px',
                            fontWeight: 600
                          }}
                        >
                          Cancel
                        </button>
                      )}
                      <button
                        onClick={() => downloadPdf(inv)}
                        style={{
                          padding: '4px 8px',
                          background: '#EFF6FF',
                          color: '#1D4ED8',
                          border: '1px solid #BFDBFE',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: 600
                        }}
                      >
                        PDF
                      </button>
                      <a
                        href={invoiceApi.getPrintableUrl(inv.id)}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          padding: '4px 8px',
                          background: '#F3F4F6',
                          color: '#374151',
                          border: '1px solid #D1D5DB',
                          borderRadius: '4px',
                          textDecoration: 'none',
                          fontSize: '12px',
                          fontWeight: 600,
                          display: 'inline-block'
                        }}
                      >
                        Print
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Cancel Reason Modal */}
      <Modal isOpen={!!cancellingInv} onClose={() => setCancellingInv(null)} title={`Cancel Invoice ${cancellingInv?.number}`}>
        <form onSubmit={handleCancelSubmit}>
          <p style={{ color: '#6B7280', fontSize: '14px', margin: '0 0 12px 0' }}>
            Cancellation will set this invoice to terminal CANCELLED state and release any unbilled periods.
          </p>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
            Reason for Cancellation
          </label>
          <textarea
            required
            rows={3}
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="e.g. Customer billing details changed, reissuing invoice."
            style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button
              type="button"
              onClick={() => setCancellingInv(null)}
              style={{ padding: '8px 16px', border: '1px solid #D1D5DB', borderRadius: '6px', background: '#FFF', cursor: 'pointer' }}
            >
              Back
            </button>
            <button
              type="submit"
              style={{ padding: '8px 16px', background: '#DC2626', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
            >
              Confirm Cancellation
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
