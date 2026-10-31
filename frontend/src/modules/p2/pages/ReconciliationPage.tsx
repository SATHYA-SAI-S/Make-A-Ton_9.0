import React, { useEffect, useState } from 'react';
import type { reconciliationApi } from '../api';
import type { ReconciliationReport } from '../types';
import type { Card, Badge, StatCard } from '../components';

export const ReconciliationPage: React.FC = () => {
  const [report, setReport] = useState<ReconciliationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAllocating, setIsAllocating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await reconciliationApi.getReport();
      setReport(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load reconciliation report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, []);

  const handleAutoAllocate = async () => {
    if (!window.confirm('Run FIFO auto-allocation of unallocated credits to oldest unpaid invoices?')) return;
    try {
      setIsAllocating(true);
      const res = await reconciliationApi.autoAllocate();
      alert(`Auto-Allocation Complete!\n\nAllocations Created: ${res.allocations_made}\nTotal Settled: ₹${res.total_allocated}`);
      await loadReport();
    } catch (err: any) {
      alert(`Auto-allocation failed: ${err.message}`);
    } finally {
      setIsAllocating(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#111827' }}>Financial Reconciliation Audit</h1>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            Comprehensive verification comparing payments, allocations, invoice balances, and orphaned credits
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={loadReport}
            style={{
              backgroundColor: '#FFFFFF',
              color: '#374151',
              border: '1px solid #D1D5DB',
              borderRadius: '6px',
              padding: '10px 16px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            ↻ Refresh Audit
          </button>
          <button
            onClick={handleAutoAllocate}
            disabled={isAllocating}
            style={{
              backgroundColor: '#059669',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '6px',
              padding: '10px 16px',
              fontWeight: 600,
              cursor: isAllocating ? 'not-allowed' : 'pointer'
            }}
          >
            {isAllocating ? 'Allocating...' : '⚡ Auto-Allocate Unallocated Credits'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div>Running reconciliation audit...</div>
      ) : report ? (
        <>
          {/* Health Banner */}
          <div
            style={{
              padding: '16px 20px',
              borderRadius: '8px',
              backgroundColor: report.is_healthy ? '#ECFDF5' : '#FEF2F2',
              border: `1px solid ${report.is_healthy ? '#A7F3D0' : '#FECACA'}`,
              marginBottom: '24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: '16px', color: report.is_healthy ? '#065F46' : '#991B1B' }}>
                {report.is_healthy ? '✓ Ledger is 100% Balanced and Reconciled' : '⚠️ Discrepancies Detected in Financial Records'}
              </div>
              <div style={{ fontSize: '13px', color: report.is_healthy ? '#047857' : '#B91C1C', marginTop: '2px' }}>
                {report.is_healthy
                  ? 'All payments, split allocations, invoice balances, and credit reserves match perfectly with zero drift.'
                  : `${report.discrepancies_count} inconsistencies require review below.`}
              </div>
            </div>
            <Badge status={report.is_healthy ? 'HEALTHY' : 'MISMATCH'} variant={report.is_healthy ? 'success' : 'danger'} />
          </div>

          {/* Metrics Row */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
            <StatCard
              title="Total Payments Captured"
              value={`₹${parseFloat(report.metrics.total_payment_volume).toFixed(2)}`}
              subtitle={`${report.total_payments_checked} payments verified`}
              variant="success"
            />
            <StatCard
              title="Unallocated Customer Credit"
              value={`₹${parseFloat(report.metrics.total_unallocated_volume).toFixed(2)}`}
              subtitle="Advances available to allocate"
              variant="info"
            />
            <StatCard
              title="Outstanding Invoices"
              value={`₹${parseFloat(report.metrics.total_invoice_balance).toFixed(2)}`}
              subtitle={`${report.total_invoices_checked} invoices audited`}
              variant="warning"
            />
          </div>

          {/* Discrepancies Card */}
          <Card
            title={report.is_healthy ? 'Audit Results' : `Identified Discrepancies (${report.discrepancies_count})`}
            subtitle={`Checked as of ${new Date(report.timestamp).toLocaleString()}`}
          >
            {report.discrepancies.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px', color: '#059669', fontWeight: 500 }}>
                ✓ No errors, orphaned payments, or unallocated balance drift discovered.
              </div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
                    <th style={{ padding: '10px 12px' }}>Type</th>
                    <th style={{ padding: '10px 12px' }}>Entity ID</th>
                    <th style={{ padding: '10px 12px' }}>Discrepancy Description</th>
                  </tr>
                </thead>
                <tbody>
                  {report.discrepancies.map((d, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #F3F4F6', fontSize: '14px' }}>
                      <td style={{ padding: '12px' }}>
                        <Badge status={d.type} variant="danger" />
                      </td>
                      <td style={{ padding: '12px', fontFamily: 'monospace', color: '#4B5563' }}>{d.entity_id}</td>
                      <td style={{ padding: '12px', color: '#DC2626', fontWeight: 500 }}>{d.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
};
