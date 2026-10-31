import React, { useEffect, useState } from 'react';
import { taxApi } from '../api';
import { TaxRule, BillingSettings } from '../types';
import { Card, Badge, Modal } from '../components';

export const TaxManagementPage: React.FC = () => {
  const [rules, setRules] = useState<TaxRule[]>([]);
  const [settings, setSettings] = useState<BillingSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Rule Modal state
  const [showModal, setShowModal] = useState(false);
  const [newRule, setNewRule] = useState({
    name: '',
    rate: '18.00',
    type: 'GST' as const,
    effective_from: new Date().toISOString().split('T')[0]
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [rulesData, settingsData] = await Promise.all([
        taxApi.getRules(),
        taxApi.getSettings()
      ]);
      setRules(rulesData);
      setSettings(settingsData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load tax data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await taxApi.createRule(newRule);
      setShowModal(false);
      setNewRule({ name: '', rate: '18.00', type: 'GST', effective_from: new Date().toISOString().split('T')[0] });
      await loadData();
    } catch (err: any) {
      alert(`Error creating tax rule: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#111827' }}>Tax Management</h1>
          <p style={{ margin: '4px 0 0 0', color: '#6B7280' }}>
            GST & place-of-supply rules (Intra-state CGST+SGST vs Inter-state IGST)
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
          + Add Tax Rule
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', backgroundColor: '#FEE2E2', color: '#991B1B', borderRadius: '6px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Company Seller Settings */}
      <Card title="Billing & Place-of-Supply Company Profile" subtitle="Determines seller origin state for GST split calculations">
        {settings ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div>
              <span style={{ fontSize: '12px', color: '#6B7280', textTransform: 'uppercase' }}>Company Name</span>
              <div style={{ fontWeight: 600, color: '#111827' }}>{settings.company_name}</div>
            </div>
            <div>
              <span style={{ fontSize: '12px', color: '#6B7280', textTransform: 'uppercase' }}>Seller State Code</span>
              <div style={{ fontWeight: 600, color: '#111827' }}>
                <Badge status={settings.company_state_code} variant="info" />
              </div>
            </div>
            <div>
              <span style={{ fontSize: '12px', color: '#6B7280', textTransform: 'uppercase' }}>GSTIN</span>
              <div style={{ fontWeight: 600, color: '#111827' }}>{settings.company_gstin || 'None (Unregistered)'}</div>
            </div>
            <div>
              <span style={{ fontSize: '12px', color: '#6B7280', textTransform: 'uppercase' }}>Currency</span>
              <div style={{ fontWeight: 600, color: '#111827' }}>{settings.default_currency}</div>
            </div>
          </div>
        ) : (
          <div>Loading company profile...</div>
        )}
      </Card>

      {/* Tax Rules Table */}
      <Card title="Configured Tax Rules" subtitle="Applied dynamically based on buyer state and product applicability">
        {loading ? (
          <div>Loading tax rules...</div>
        ) : rules.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px', color: '#6B7280' }}>No tax rules configured yet.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #E5E7EB', color: '#4B5563', fontSize: '13px' }}>
                <th style={{ padding: '10px 12px' }}>Name</th>
                <th style={{ padding: '10px 12px' }}>Type</th>
                <th style={{ padding: '10px 12px' }}>Rate</th>
                <th style={{ padding: '10px 12px' }}>Effective From</th>
                <th style={{ padding: '10px 12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id} style={{ borderBottom: '1px solid #F3F4F6', fontSize: '14px' }}>
                  <td style={{ padding: '12px', fontWeight: 600, color: '#111827' }}>{rule.name}</td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={rule.type} />
                  </td>
                  <td style={{ padding: '12px', fontWeight: 600 }}>{rule.rate}%</td>
                  <td style={{ padding: '12px', color: '#6B7280' }}>{rule.effective_from}</td>
                  <td style={{ padding: '12px' }}>
                    <Badge status={rule.active ? 'ACTIVE' : 'INACTIVE'} variant={rule.active ? 'success' : 'neutral'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Create Tax Rule Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Create New Tax Rule">
        <form onSubmit={handleCreateRule} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Rule Name</label>
            <input
              type="text"
              required
              value={newRule.name}
              onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
              placeholder="e.g. Standard GST 18%"
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Rate (%)</label>
              <input
                type="number"
                step="0.01"
                required
                value={newRule.rate}
                onChange={(e) => setNewRule({ ...newRule, rate: e.target.value })}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Type</label>
              <select
                value={newRule.type}
                onChange={(e) => setNewRule({ ...newRule, type: e.target.value as any })}
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
              >
                <option value="GST">GST (Intra CGST+SGST / Inter IGST)</option>
                <option value="IGST">IGST</option>
                <option value="VAT">VAT</option>
                <option value="CUSTOM">CUSTOM</option>
              </select>
            </div>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>Effective From</label>
            <input
              type="date"
              required
              value={newRule.effective_from}
              onChange={(e) => setNewRule({ ...newRule, effective_from: e.target.value })}
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: '6px' }}
            />
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
              Save Rule
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
