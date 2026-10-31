export interface NavItem {
  label: string;
  path: string;
  module: string;
}

export const nav: NavItem[] = [
  { label: 'Portal Dashboard', path: '/portal', module: 'p3' },
  { label: 'My Subscriptions', path: '/portal/subscriptions', module: 'p3' },
  { label: 'My Invoices', path: '/portal/invoices', module: 'p3' },
  { label: 'Payment Ledger', path: '/portal/payments', module: 'p3' },
  { label: 'Account Profile', path: '/portal/profile', module: 'p3' },
  { label: 'Finance Intelligence', path: '/p3/finance', module: 'p3' },
  { label: 'Revenue Analytics', path: '/p3/finance/revenue', module: 'p3' },
  { label: 'Subscription Analytics', path: '/p3/finance/subscriptions', module: 'p3' },
  { label: 'Collection & Risk', path: '/p3/finance/collections', module: 'p3' },
  { label: 'Cohort Retention', path: '/p3/finance/cohorts', module: 'p3' },
  { label: 'Revenue Concentration', path: '/p3/finance/concentration', module: 'p3' },
  { label: 'UI Demo', path: '/ui-demo', module: 'p3' },
];
