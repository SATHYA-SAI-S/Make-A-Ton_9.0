import React, { useEffect, useState } from 'react';
import { discountApi } from '../api';
import { DiscountRule } from '../types';
import { Card, Badge, Modal, StatCard } from '../components';

export const DiscountManagementPage: React.FC = () => {
  const [discounts, setDiscounts] = useState<DiscountRule[]>([]);
  const [performance, setPerformance] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Discount Modal state
  const [showModal, setShowModal] = useState(false);
  const [newDiscount, setNewDiscount] = useState({
    code: '',
    name: '',
    discount_type: 'PERCENTAGE' as const,
    value: '10.00',
    scope: 'SUBSCRIPTION' as const,
    max_discount_amount: '',
    max_uses: '',
    valid_from: new Date().toISOString().split('T')[0]
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [discData, perfData] = await Promise.all([
        discountApi.getDiscounts(),
        discountApi.getPerformance().catch(() => [])
      ]);
      setDiscounts(discData);
      setPerformance(perfData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load discount data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await discountApi.createDiscount({
        code: newDiscount.code.toUpperCase(),
        name: newDiscount.name,
        discount_type: newDiscount.discount_type,
        value: newDiscount.value,
        scope: newDiscount.scope,
        max_discount_amount: newDiscount.max_discount_amount ? newDiscount.max_discount_amount : null,
        max_uses: newDiscount.max_uses ? parseInt(newDiscount.max_uses, 10) : null,
        valid_from: newDiscount.valid_from
      });
      setShowModal(false);
      setNewDiscount({
        code: '',
        name: '',
        discount_type: 'PERCENTAGE',
        value: '10.00',
        scope: 'SUBSCRIPTION',
        max_discount_amount: '',
        max_uses: '',
        valid_from: new Date().toISOString().split('T')[0]
      });
      await loadData();
    } catch (err: any) {
      alert(`Error creating discount: ${err.message}`);
    }
  };

  const totalRedemptions = performance.reduce((sum, p) => sum + (p.times_redeemed || 0), 0);
  const totalSavings = performance.reduce((sum, p) => sum + parseFloat(p.total_discount_amount || '0'), 0);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#111827' }}>Discount Management</h1>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            Coupon codes, promotional rules, and redemption usage tracking
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
          + Create Discount
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Metrics Row */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <StatCard title="Active Rules" value={discounts.filter((d) => d.active).length} subtitle="Live in billing engine" variant="success" />
        <StatCard title="Total Redemptions" value={totalRedemptions} subtitle="Across all billing periods" variant="info" />
        <StatCard title="Customer Savings" value={`₹${totalSavings.toFixed(2)}`} subtitle="Total value discounted" variant="warning" />
      </div>

      {/* Discounts Table */}
      <Card title="Available Discount Rules" subtitle="Coupons and automatic price adjustments applied during invoicing">
        {loading ? (
          <div>Loading discounts...</div>
        ) : discounts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#6B7280' }}>No discount rules configured yet.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
                <th style={{ padding: '10px 12px' }}>Code</th>
                <th style={{ padding: '10px 12px' }}>Name</th>
                <th style={{ padding: '10px 12px' }}>Type & Value</th>
                <th style={{ padding: '10px 12px' }}>Scope</th>
                <th style={{ padding: '10px 12px' }}>Usage</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {discounts.map((disc) => (
                <tr key={disc.id} style={{ borderBottom: '1px solid #F3F4F6', fontSize: '14px' }}>
                  <td style={{ padding: '12px', fontWeight: 700, color: '#1E40AF', fontFamily: 'monospace' }}>{disc.code}</td>
                  <td style={{ padding: '12px', fontWeight: 500, color: '#111827' }}>{disc.name}</td>
                  <td style={{ padding: '12px', fontWeight: 600 }}>
                    {disc.discount_type === 'PERCENTAGE' ? `${disc.value}%` : `₹${disc.value}`}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={disc.scope} variant="neutral" />
                  </td>
                  <td style={{ padding: '12px', color: '#4B5563' }}>
                    {disc.current_uses} {disc.max_uses ? `/ ${disc.max_uses}` : 'uses'}
                  </td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={disc.active ? 'ACTIVE' : 'EXPIRED'} variant={disc.active ? 'success' : 'neutral'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Create Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Create New Discount Rule">
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Code</label>
              <input
                type="text"
                required
                value={newDiscount.code}
                onChange={(e) => setNewDiscount({ ...newDiscount, code: e.target.value })}
                placeholder="e.g. FESTIVE20"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Rule Name</label>
              <input
                type="text"
                required
                value={newDiscount.name}
                onChange={(e) => setNewDiscount({ ...newDiscount, name: e.target.value })}
                placeholder="e.g. Diwali Festive Offer"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Type</label>
              <select
                value={newDiscount.discount_type}
                onChange={(e) => setNewDiscount({ ...newDiscount, discount_type: e.target.value as any })}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              >
                <option value="PERCENTAGE">Percentage (%)</option>
                <option value="FIXED">Fixed Amount (₹)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Value</label>
              <input
                type="number"
                step="0.01"
                required
                value={newDiscount.value}
                onChange={(e) => setNewDiscount({ ...newDiscount, value: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Scope</label>
              <select
                value={newDiscount.scope}
                onChange={(e) => setNewDiscount({ ...newDiscount, scope: e.target.value as any })}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              >
                <option value="SUBSCRIPTION">Whole Subscription</option>
                <option value="PRODUCT">Specific Product</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Max Uses (Optional)</label>
              <input
                type="number"
                value={newDiscount.max_uses}
                onChange={(e) => setNewDiscount({ ...newDiscount, max_uses: e.target.value })}
                placeholder="Unlimited if empty"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
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
              Save Discount
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
