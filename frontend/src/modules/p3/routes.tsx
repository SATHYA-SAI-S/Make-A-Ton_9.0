import React from 'react';
import { RouteObject } from 'react-router-dom';
import { UiDemo } from './pages/UiDemo';
import { CustomerDashboard } from './pages/portal/CustomerDashboard';
import { MySubscriptions } from './pages/portal/MySubscriptions';
import { MyInvoices } from './pages/portal/MyInvoices';
import { PaymentHistory } from './pages/portal/PaymentHistory';
import { CustomerProfilePage } from './pages/portal/CustomerProfile';
import { SubscriptionTimeline } from './pages/portal/SubscriptionTimeline';
import { FinanceOverview } from './pages/finance/FinanceOverview';
import { RevenueAnalytics } from './pages/finance/RevenueAnalytics';
import { SubscriptionAnalytics } from './pages/finance/SubscriptionAnalytics';
import { CollectionAnalytics } from './pages/finance/CollectionAnalytics';
import { DrilldownInvoices } from './pages/finance/DrilldownInvoices';
import { CohortRetentionPage } from './pages/finance/CohortRetentionPage';
import { RevenueConcentrationPage } from './pages/finance/RevenueConcentrationPage';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <CustomerDashboard />,
  },
  {
    path: '/ui-demo',
    element: <UiDemo />,
  },
  {
    path: '/portal',
    element: <CustomerDashboard />,
  },
  {
    path: '/portal/subscriptions',
    element: <MySubscriptions />,
  },
  {
    path: '/portal/invoices',
    element: <MyInvoices />,
  },
  {
    path: '/portal/payments',
    element: <PaymentHistory />,
  },
  {
    path: '/portal/profile',
    element: <CustomerProfilePage />,
  },
  {
    path: '/portal/timeline',
    element: <SubscriptionTimeline />,
  },
  {
    path: '/p3/finance',
    element: <FinanceOverview />,
  },
  {
    path: '/p3/finance/overview',
    element: <FinanceOverview />,
  },
  {
    path: '/p3/finance/revenue',
    element: <RevenueAnalytics />,
  },
  {
    path: '/p3/finance/subscriptions',
    element: <SubscriptionAnalytics />,
  },
  {
    path: '/p3/finance/collections',
    element: <CollectionAnalytics />,
  },
  {
    path: '/p3/finance/invoices',
    element: <DrilldownInvoices />,
  },
  {
    path: '/p3/finance/cohorts',
    element: <CohortRetentionPage />,
  },
  {
    path: '/p3/finance/concentration',
    element: <RevenueConcentrationPage />,
  },
];
