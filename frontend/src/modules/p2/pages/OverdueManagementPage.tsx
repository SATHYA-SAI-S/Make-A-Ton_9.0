import React, { useEffect, useState } from 'react';
import { overdueApi } from '../api';
import { OverdueInvoice, OverdueSummary, PaymentFollowup } from '../types';
import { Card, Badge, Modal, StatCard } from '../components';

export const OverdueManagementPage: React.FC = () => {
  const [invoices, setInvoices] = useState<OverdueInvoice[]>([]);
  const [summary, setSummary] = useState<OverdueSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Follow-up modal state
  const [followupInv, setFollowupInv] = useState<OverdueInvoice | null>(null);
  const [notes, setNotes] = useState('');
  const [promisedDate, setPromisedDate] = useState('');
  const [channel, setChannel] = useState('PHONE');
  const [followupStatus, setFollowupStatus] = useState('PROMISED');

  // Follow-up history modal state
  const [historyInv, setHistoryInv] = useState<OverdueInvoice | null>(null);
  const [historyList, setHistoryList] = useState<PaymentFollowup[]>([]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [invData, sumData] = await Promise.all([
        overdueApi.getOverdueInvoices(),
        overdueApi.getSummary()
      ]);
      setInvoices(invData || []);
      setSummary(sumData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load overdue tracking data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTriggerReminders = async () => {
    try {
      const res = await overdueApi.triggerReminders();
      alert(
        `Automated Reminders Evaluation Finished!\n\n` +
        `Invoices Evaluated: ${res.invoices_evaluated}\n` +
        `Reminders Sent: ${res.reminders_sent}\n` +
        `Reminders Skipped (Already Sent): ${res.reminders_skipped}`
      );
      await loadData();
    } catch (err: any) {
      alert(`Reminder trigger failed: ${err.message}`);
    }
  };

  const handleFollowupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!followupInv) return;
    try {
      await overdueApi.createFollowup({
        invoice_id: followupInv.invoice_id,
        notes,
        promised_payment_date: promisedDate || undefined,
        channel,
        status: followupStatus
      });
      setFollowupInv(null);
      setNotes('');
      setPromisedDate('');
      await loadData();
    } catch (err: any) {
      alert(`Error saving follow-up: ${err.message}`);
    }
  };

  const openHistory = async (inv: OverdueInvoice) => {
    setHistoryInv(inv);
    try {
      const list = await overdueApi.getFollowups(inv.invoice_id);
      setHistoryList(list);
    } catch (err: any) {
      alert(`Failed to load history: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#111827' }}>Overdue Management & Dunning</h1>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            Multi-tier escalation (Tier 1 gentle, Tier 2 firm, Tier 3 urgent notice) and collection tracking
          </p>
        </div>
        <button
          onClick={handleTriggerReminders}
          style={{
            backgroundColor: '#DC2626',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '6px',
            padding: '10px 16px',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          ⚡ Evaluate & Send Due Reminders
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Metrics Row */}
      {summary && (
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
          <StatCard
            title="Total Overdue Amount"
            value={`₹${parseFloat(summary.total_overdue_amount).toFixed(2)}`}
            subtitle={`${summary.total_overdue_count} overdue invoices`}
            variant="danger"
          />
          <StatCard
            title="Tier 1 (1–7 Days)"
            value={summary.tiers.tier_1.count}
            subtitle={`₹${parseFloat(summary.tiers.tier_1.amount).toFixed(2)} gentle reminder`}
            variant="warning"
          />
          <StatCard
            title="Tier 2 (8–14 Days)"
            value={summary.tiers.tier_2.count}
            subtitle={`₹${parseFloat(summary.tiers.tier_2.amount).toFixed(2)} formal notice`}
            variant="info"
          />
          <StatCard
            title="Tier 3 (15+ Days)"
            value={summary.tiers.tier_3.count}
            subtitle={`₹${parseFloat(summary.tiers.tier_3.amount).toFixed(2)} suspension alert`}
            variant="danger"
          />
        </div>
      )}

      {/* Overdue Table */}
      <Card title="Overdue Invoices">
        {loading ? (
          <div>Loading overdue list...</div>
        ) : invoices.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#059669', fontWeight: 600 }}>
            🎉 Great job! No overdue invoices found.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
                <th style={{ padding: '10px 12px' }}>Invoice #</th>
                <th style={{ padding: '10px 12px' }}>Customer</th>
                <th style={{ padding: '10px 12px' }}>Due Date</th>
                <th style={{ padding: '10px 12px' }}>Overdue</th>
                <th style={{ padding: '10px 12px' }}>Tier</th>
                <th style={{ padding: '10px 12px' }}>Balance</th>
                <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.invoice_id} style={{ borderBottom: '1px solid #F3F4F6', fontSize: '14px' }}>
                  <td style={{ padding: '12px', fontWeight: 700, fontFamily: 'monospace', color: '#1E40AF' }}>
                    {inv.invoice_number}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <div style={{ fontWeight: 600, color: '#111827' }}>{inv.customer_name}</div>
                    <div style={{ fontSize: '12px', color: '#6B7280' }}>{inv.customer_email || inv.customer_id}</div>
                  </td>
                  <td style={{ padding: '12px', color: '#4B5563' }}>{inv.due_date}</td>
                  <td style={{ padding: '12px', fontWeight: 600, color: '#DC2626' }}>{inv.days_overdue} days</td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={`TIER ${inv.tier}`} variant={inv.tier === 3 ? 'danger' : inv.tier === 2 ? 'info' : 'warning'} />
                  </td>
                  <td style={{ padding: '12px', fontWeight: 700, color: '#DC2626' }}>₹{inv.balance}</td>
                  <td style={{ padding: '12px', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      <button
                        onClick={() => setFollowupInv(inv)}
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
                        Log Follow-up
                      </button>
                      <button
                        onClick={() => openHistory(inv)}
                        style={{
                          padding: '4px 8px',
                          background: '#F3F4F6',
                          color: '#374151',
                          border: '1px solid #D1D5DB',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: 600
                        }}
                      >
                        History
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Log Follow-up Modal */}
      <Modal isOpen={!!followupInv} onClose={() => setFollowupInv(null)} title={`Log Follow-up: ${followupInv?.invoice_number}`}>
        <form onSubmit={handleFollowupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Contact Channel</label>
              <select
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              >
                <option value="PHONE">Phone Call</option>
                <option value="EMAIL">Email</option>
                <option value="SMS">SMS / WhatsApp</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Status</label>
              <select
                value={followupStatus}
                onChange={(e) => setFollowupStatus(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              >
                <option value="PROMISED">Payment Promised</option>
                <option value="PENDING">Pending Response</option>
                <option value="DISPUTED">Disputed Invoice</option>
                <option value="RESOLVED">Resolved</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Promised Payment Date (Optional)</label>
            <input
              type="date"
              value={promisedDate}
              onChange={(e) => setPromisedDate(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Call Notes / Outcome</label>
            <textarea
              required
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Spoke with CFO, agreed to clear balance by Friday via NEFT."
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button
              type="button"
              onClick={() => setFollowupInv(null)}
              style={{ padding: '8px 16px', border: '1px solid #D1D5DB', borderRadius: '6px', background: '#FFF', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{ padding: '8px 16px', background: '#2563EB', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}
            >
              Save Follow-up
            </button>
          </div>
        </form>
      </Modal>

      {/* History Modal */}
      <Modal isOpen={!!historyInv} onClose={() => setHistoryInv(null)} title={`Follow-up History: ${historyInv?.invoice_number}`} width="650px">
        {historyList.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: '#6B7280' }}>No previous follow-up records logged.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {historyList.map((h) => (
              <div key={h.id} style={{ border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <Badge status={h.channel} variant="neutral" />
                    <Badge status={h.status} />
                  </div>
                  <span style={{ fontSize: '12px', color: '#6B7280' }}>{new Date(h.created_at).toLocaleString()}</span>
                </div>
                <div style={{ fontSize: '14px', color: '#111827', margin: '6px 0' }}>{h.notes}</div>
                {h.promised_payment_date && (
                  <div style={{ fontSize: '12px', color: '#059669', fontWeight: 600 }}>
                    Promised Date: {h.promised_payment_date}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};
