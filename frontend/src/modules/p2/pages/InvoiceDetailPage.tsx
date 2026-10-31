import React, { useEffect, useState } from 'react';
import type { invoiceApi } from '../api';
import type { Invoice } from '../types';
import type { Card, Badge } from '../components';

export const InvoiceDetailPage: React.FC<{
  invoiceId: string;
  onBack: () => void;
}> = ({ invoiceId, onBack }) => {
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showJsonSnapshot, setShowJsonSnapshot] = useState(false);

  useEffect(() => {
    const loadInvoice = async () => {
      try {
        setLoading(true);
        const data = await invoiceApi.getInvoice(invoiceId);
        setInvoice(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load invoice details');
      } finally {
        setLoading(false);
      }
    };
    loadInvoice();
  }, [invoiceId]);

  if (loading) return <div style={{ padding: '32px', textAlign: 'center' }}>Loading invoice details...</div>;
  if (error || !invoice) return <div style={{ padding: '32px', color: '#DC2626' }}>{error || 'Invoice not found'}</div>;

  const snapshot = invoice.snapshot || {};
  const seller = snapshot.company || {};
  const buyer = snapshot.customer || {};

  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <button
        onClick={onBack}
        style={{
          background: 'none',
          border: 'none',
          color: '#2563EB',
          fontSize: '14px',
          fontWeight: 600,
          cursor: 'pointer',
          marginBottom: '16px',
          padding: 0
        }}
      >
        ← Back to Invoices
      </button>

      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ margin: 0, fontSize: '26px', fontWeight: 700, color: '#111827' }}>
              Invoice {invoice.number}
            </h1>
            <Badge status={invoice.status} />
            {invoice.is_overdue && <Badge status="OVERDUE" variant="danger" />}
          </div>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            Issued on {invoice.invoice_date} • Payment due by {invoice.due_date}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setShowJsonSnapshot(!showJsonSnapshot)}
            style={{
              padding: '8px 14px',
              border: '1px solid #D1D5DB',
              borderRadius: '6px',
              backgroundColor: '#FFFFFF',
              color: '#374151',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            {showJsonSnapshot ? 'Hide Snapshot' : 'View Snapshot JSON'}
          </button>
          <a
            href={invoiceApi.getPrintableUrl(invoice.id)}
            target="_blank"
            rel="noreferrer"
            style={{
              padding: '8px 14px',
              border: '1px solid #2563EB',
              borderRadius: '6px',
              backgroundColor: '#2563EB',
              color: '#FFFFFF',
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-block'
            }}
          >
            Print / PDF
          </a>
        </div>
      </div>

      {/* Snapshot JSON viewer */}
      {showJsonSnapshot && (
        <Card title="Immutable Audit Snapshot JSON" subtitle="Exact state of tax rules, products, and parties when finalized">
          <pre style={{ backgroundColor: '#F3F4F6', padding: '16px', borderRadius: '6px', fontSize: '12px', overflowX: 'auto' }}>
            {JSON.stringify(invoice.snapshot, null, 2)}
          </pre>
        </Card>
      )}

      {/* Seller & Customer Information Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        <Card title="Seller (Brightloop)">
          <div style={{ fontSize: '14px', color: '#374151', lineHeight: '1.6' }}>
            <div style={{ fontWeight: 600, color: '#111827' }}>{seller.name || 'Brightloop Software Private Limited'}</div>
            <div>GSTIN: {seller.gstin || '-'}</div>
            <div>State Code: {seller.state_code || 'KA'}</div>
          </div>
        </Card>

        <Card title="Billed To">
          <div style={{ fontSize: '14px', color: '#374151', lineHeight: '1.6' }}>
            <div style={{ fontWeight: 600, color: '#111827' }}>{buyer.name || 'Customer'}</div>
            <div>Email: {buyer.email || '-'}</div>
            <div>GSTIN: {buyer.gstin || 'Unregistered'}</div>
            <div>State Code: {buyer.state_code || '-'}</div>
          </div>
        </Card>
      </div>

      {/* Line Items */}
      <Card title="Line Items">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
              <th style={{ padding: '10px 8px' }}>Description</th>
              <th style={{ padding: '10px 8px', textAlign: 'center' }}>Qty</th>
              <th style={{ padding: '10px 8px', textAlign: 'right' }}>Unit Price</th>
              <th style={{ padding: '10px 8px', textAlign: 'right' }}>Discount</th>
              <th style={{ padding: '10px 8px', textAlign: 'right' }}>Tax</th>
              <th style={{ padding: '10px 8px', textAlign: 'right' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {(invoice.lines || []).map((l) => (
              <tr key={l.id} style={{ borderBottom: '1px solid #F3F4F6' }}>
                <td style={{ padding: '12px 8px', fontWeight: 500, color: '#111827' }}>{l.description}</td>
                <td style={{ padding: '12px 8px', textAlign: 'center' }}>{l.quantity}</td>
                <td style={{ padding: '12px 8px', textAlign: 'right' }}>₹{l.unit_price}</td>
                <td style={{ padding: '12px 8px', textAlign: 'right', color: '#059669' }}>-₹{l.discount_amount}</td>
                <td style={{ padding: '12px 8px', textAlign: 'right' }}>₹{l.tax_amount} ({l.tax_rate}%)</td>
                <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 600 }}>₹{l.line_total}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Totals Breakdown */}
        <div style={{ marginTop: '20px', borderTop: '2px solid #E5E7EB', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
          <div style={{ width: '280px', fontSize: '14px', lineHeight: '2' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#4B5563' }}>
              <span>Subtotal:</span>
              <span style={{ fontWeight: 600 }}>₹{invoice.subtotal}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#059669' }}>
              <span>Discounts:</span>
              <span style={{ fontWeight: 600 }}>-₹{invoice.discount_total}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#4B5563' }}>
              <span>Taxes (GST):</span>
              <span style={{ fontWeight: 600 }}>₹{invoice.tax_total}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '16px', fontWeight: 700, color: '#111827', borderTop: '1px solid #D1D5DB', marginTop: '6px', paddingTop: '6px' }}>
              <span>Grand Total:</span>
              <span>₹{invoice.total}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#059669' }}>
              <span>Amount Paid:</span>
              <span style={{ fontWeight: 600 }}>₹{invoice.amount_paid}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: parseFloat(invoice.balance) > 0 ? '#DC2626' : '#111827', fontWeight: 700, fontSize: '15px' }}>
              <span>Remaining Balance:</span>
              <span>₹{invoice.balance}</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
