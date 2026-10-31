export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  description?: string;
}

export const P2_NAV_ITEMS: NavItem[] = [
  {
    id: 'invoices',
    label: 'Invoices',
    path: '/billing/invoices',
    description: 'Invoicing lifecycle, PDF & print generation'
  },
  {
    id: 'billing-control',
    label: 'Billing Engine',
    path: '/billing/control',
    description: 'Advisory-locked recurring run execution'
  },
  {
    id: 'payments',
    label: 'Payments',
    path: '/billing/payments',
    description: 'Capture, split allocations & refunds'
  },
  {
    id: 'overdue',
    label: 'Overdue & Dunning',
    path: '/billing/overdue',
    description: 'Multi-tier escalation and follow-up tracking'
  },
  {
    id: 'reconciliation',
    label: 'Reconciliation',
    path: '/billing/reconciliation',
    description: 'Ledger audit and auto-allocation'
  },
  {
    id: 'taxes',
    label: 'Tax Rules',
    path: '/billing/taxes',
    description: 'Place-of-supply rules & company profile'
  },
  {
    id: 'discounts',
    label: 'Discounts',
    path: '/billing/discounts',
    description: 'Promo codes & usage limits'
  }
];
