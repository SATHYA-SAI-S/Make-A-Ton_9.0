import React, { useEffect, useState } from 'react';
import { paymentApi, invoiceApi } from '../api';
import { Payment, PaymentMethod, Invoice } from '../types';
import { Card, Badge, Modal, StatCard } from '../components';

export const PaymentManagementPage: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Record Payment Modal State
  const [showModal, setShowModal] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [method, setMethod] = useState<PaymentMethod>('UPI');
  const [amount, setAmount] = useState('1000.00');
  const [reference, setReference] = useState('');
  const [notes, setNotes] = useState('');
  const [allocations, setAllocations] = useState<{ invoice_id: string; amount: string }[]>([]);

  // Open invoices for customer
  const [customerInvoices, setCustomerInvoices] = useState<Invoice[]>([]);

  // Refund Modal State
  const [refundingPayment, setRefundingPayment] = useState<Payment | null>(null);
  const [refundAmount, setRefundAmount] = useState('');
  const [refundReason, setRefundReason] = useState('');

  const loadPayments = async () => {
    try {
      setLoading(true);
      const res = await paymentApi.getPayments();
      setPayments(res.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, []);

  const handleCustomerBlur = async () => {
    if (!customerId) return;
    try {
      const res = await invoiceApi.getInvoices({ customer_id: customerId });
      // Only unpaid invoices
      const unpaid = (res.items || []).filter((inv) => ['CONFIRMED', 'PARTIALLY_PAID'].includes(inv.status));
      setCustomerInvoices(unpaid);
    } catch (_) {}
  };

  const addAllocationRow = () => {
    setAllocations([...allocations, { invoice_id: '', amount: '0.00' }]);
  };

  const removeAllocationRow = (index: number) => {
    setAllocations(allocations.filter((_, i) => i !== index));
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const validAllocs = allocations.filter((a) => a.invoice_id && parseFloat(a.amount) > 0);
      await paymentApi.recordPayment({
        customer_id: customerId,
        method,
        amount,
        reference: reference || undefined,
        notes: notes || undefined,
        allocations: validAllocs.length > 0 ? validAllocs : undefined
      });
      setShowModal(false);
      setCustomerId('');
      setAmount('1000.00');
      setReference('');
      setAllocations([]);
      await loadPayments();
    } catch (err: any) {
      alert(`Error recording payment: ${err.message}`);
    }
  };

  const handleRefundSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refundingPayment) return;
    try {
      await paymentApi.refundPayment(refundingPayment.id, refundAmount, refundReason);
      setRefundingPayment(null);
      setRefundAmount('');
      setRefundReason('');
      await loadPayments();
    } catch (err: any) {
      alert(`Refund failed: ${err.message}`);
    }
  };

  const totalCollected = payments.reduce((acc, p) => acc + (p.status === 'RECORDED' ? parseFloat(p.amount) : 0), 0);
  const totalUnallocated = payments.reduce((acc, p) => acc + (p.status === 'RECORDED' ? parseFloat(p.unallocated_amount) : 0), 0);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#111827' }}>Payment Management</h1>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            Multi-method capture, split payment allocations across invoices, refunds, and advance credits
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          style={{
            backgroundColor: '#2563EB',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '6px',
            padding: '10px 16px',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          + Record Payment
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Metrics Row */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <StatCard title="Total Collected" value={`₹${totalCollected.toFixed(2)}`} subtitle="Successfully captured" variant="success" />
        <StatCard title="Unallocated Advances" value={`₹${totalUnallocated.toFixed(2)}`} subtitle="Surplus credit balance" variant="info" />
        <StatCard title="Recorded Transactions" value={payments.length} subtitle="Payments logged" />
      </div>

      {/* Payments Table */}
      <Card title="Payment History">
        {loading ? (
          <div>Loading payments...</div>
        ) : payments.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#6B7280' }}>No payments recorded yet.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
                <th style={{ padding: '10px 12px' }}>Payment ID</th>
                <th style={{ padding: '10px 12px' }}>Customer</th>
                <th style={{ padding: '10px 12px' }}>Method</th>
                <th style={{ padding: '10px 12px' }}>Amount</th>
                <th style={{ padding: '10px 12px' }}>Unallocated</th>
                <th style={{ padding: '10px 12px' }}>Reference</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid #F3F4F6', fontSize: '14px' }}>
                  <td style={{ padding: '12px', fontFamily: 'monospace', color: '#4B5563' }}>{p.id.substring(0, 8)}...</td>
                  <td style={{ padding: '12px', fontWeight: 600 }}>{p.customer_id}</td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={p.method} variant="info" />
                  </td>
                  <td style={{ padding: '12px', fontWeight: 700, color: '#065F46' }}>₹{p.amount}</td>
                  <td style={{ padding: '12px', color: parseFloat(p.unallocated_amount) > 0 ? '#1E40AF' : '#6B7280' }}>
                    ₹{p.unallocated_amount}
                  </td>
                  <td style={{ padding: '12px', color: '#6B7280' }}>{p.reference || '-'}</td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={p.status} />
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    {p.status === 'RECORDED' && (
                      <button
                        onClick={() => {
                          setRefundingPayment(p);
                          setRefundAmount(p.amount);
                        }}
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
                        Refund
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Record Payment Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Record Customer Payment" width="650px">
        <form onSubmit={handleRecordPayment} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Customer ID</label>
              <input
                type="text"
                required
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                onBlur={handleCustomerBlur}
                placeholder="e.g. cust-001"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Method</label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as PaymentMethod)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              >
                <option value="UPI">UPI</option>
                <option value="CARD">Card</option>
                <option value="BANK_TRANSFER">Bank Transfer (NEFT/RTGS)</option>
                <option value="CASH">Cash</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Payment Amount (₹)</label>
              <input
                type="number"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Transaction Reference</label>
              <input
                type="text"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                placeholder="e.g. UPI / UTR / Auth Code"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
          </div>

          {/* Split Allocations Section */}
          <div style={{ borderTop: '1px solid #E5E7EB', paddingTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#374151' }}>
                Split Allocations (Optional)
              </span>
              <button
                type="button"
                onClick={addAllocationRow}
                style={{ fontSize: '12px', color: '#2563EB', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}
              >
                + Allocate to Invoice
              </button>
            </div>

            {allocations.map((alloc, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '8px' }}>
                <select
                  value={alloc.invoice_id}
                  onChange={(e) => {
                    const copy = [...allocations];
                    copy[idx].invoice_id = e.target.value;
                    setAllocations(copy);
                  }}
                  style={{ flex: 2, padding: '6px 10px', border: '1px solid #D1D5DB', borderRadius: '6px', fontSize: '13px' }}
                >
                  <option value="">Select Invoice...</option>
                  {customerInvoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.number} (Balance: ₹{inv.balance})
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  step="0.01"
                  placeholder="Amount"
                  value={alloc.amount}
                  onChange={(e) => {
                    const copy = [...allocations];
                    copy[idx].amount = e.target.value;
                    setAllocations(copy);
                  }}
                  style={{ flex: 1, padding: '6px 10px', border: '1px solid #D1D5DB', borderRadius: '6px', fontSize: '13px' }}
                />
                <button
                  type="button"
                  onClick={() => removeAllocationRow(idx)}
                  style={{ color: '#EF4444', background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px' }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={() => setShowModal(false)}
              style={{ padding: '8px 16px', border: '1px solid #D1D5DB', borderRadius: '6px', background: '#FFF', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ padding: '8px 16px', background: '#2563EB', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
            >
              Save Payment
            </button>
          </div>
        </form>
      </Modal>

      {/* Refund Modal */}
      <Modal isOpen={!!refundingPayment} onClose={() => setRefundingPayment(null)} title="Process Refund">
        <form onSubmit={handleRefundSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Refund Amount (₹)</label>
            <input
              type="number"
              step="0.01"
              required
              value={refundAmount}
              onChange={(e) => setRefundAmount(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Reason</label>
            <input
              type="text"
              required
              value={refundReason}
              onChange={(e) => setRefundReason(e.target.value)}
              placeholder="e.g. Service cancellation or overpayment refund"
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={() => setRefundingPayment(null)}
              style={{ padding: '8px 16px', border: '1px solid #D1D5DB', borderRadius: '6px', background: '#FFF', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ padding: '8px 16px', background: '#DC2626', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
            >
              Issue Refund
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
