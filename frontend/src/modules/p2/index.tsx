import React, { useState } from 'react';
import { P2_NAV_ITEMS } from './nav';
import { TaxManagementPage } from './pages/TaxManagementPage';
import { DiscountManagementPage } from './pages/DiscountManagementPage';
import { BillingControlPage } from './pages/BillingControlPage';
import { InvoiceListPage } from './pages/InvoiceListPage';
import { InvoiceDetailPage } from './pages/InvoiceDetailPage';
import { PaymentManagementPage } from './pages/PaymentManagementPage';
import { OverdueManagementPage } from './pages/OverdueManagementPage';
import { ReconciliationPage } from './pages/ReconciliationPage';

export const BillingModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('invoices');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);

  const handleSelectInvoice = (id: string) => {
    setSelectedInvoiceId(id);
  };

  const handleBackToInvoices = () => {
    setSelectedInvoiceId(null);
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#F9FAFB', fontFamily: 'sans-serif' }}>
      {/* Top Module Navigation Bar */}
      <header
        style={{
          backgroundColor: '#FFFFFF',
          borderBottom: '1px solid #E5E7EB',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontWeight: 800, fontSize: '18px', color: '#1E40AF', padding: '16px 0' }}>
            SubscriptIQ <span style={{ color: '#4B5563', fontWeight: 500, fontSize: '14px' }}>| Billing & Invoicing</span>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '8px', overflowX: 'auto' }}>
          {P2_NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setSelectedInvoiceId(null);
              }}
              style={{
                padding: '16px 12px',
                border: 'none',
                background: 'none',
                fontSize: '14px',
                fontWeight: 600,
                color: activeTab === item.id ? '#1D4ED8' : '#4B5563',
                borderBottom: activeTab === item.id ? '2px solid #1D4ED8' : '2px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content Area */}
      <main>
        {activeTab === 'invoices' && (
          selectedInvoiceId ? (
            <InvoiceDetailPage invoiceId={selectedInvoiceId} onBack={handleBackToInvoices} />
          ) : (
            <InvoiceListPage onSelectInvoice={handleSelectInvoice} />
          )
        )}
        {activeTab === 'billing-control' && <BillingControlPage />}
        {activeTab === 'payments' && <PaymentManagementPage />}
        {activeTab === 'overdue' && <OverdueManagementPage />}
        {activeTab === 'reconciliation' && <ReconciliationPage />}
        {activeTab === 'taxes' && <TaxManagementPage />}
        {activeTab === 'discounts' && <DiscountManagementPage />}
      </main>
    </div>
  );
};

export default BillingModule;
