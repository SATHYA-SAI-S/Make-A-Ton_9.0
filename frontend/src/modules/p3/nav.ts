export interface NavItem {
  label: string;
  path: string;
  module: string;
}

export const nav: NavItem[] = [
  { label: 'UI Demo', path: '/ui-demo', module: 'p3' },
  { label: 'Finance Overview', path: '/finance', module: 'p3' },
  { label: 'Revenue Guardian', path: '/guardian', module: 'p3' },
  { label: 'Customer Portal', path: '/portal', module: 'p3' },
  { label: 'Reports', path: '/reports', module: 'p3' },
  { label: 'Audit Trail', path: '/audit', module: 'p3' },
];
