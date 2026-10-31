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
  { label: 'Activity Timeline', path: '/portal/timeline', module: 'p3' },
  { label: 'UI Demo', path: '/ui-demo', module: 'p3' },
];
