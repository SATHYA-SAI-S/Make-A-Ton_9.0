import React from 'react';
import { RouteObject } from 'react-router-dom';
import { UiDemo } from './pages/UiDemo';
import { CustomerDashboard } from './pages/portal/CustomerDashboard';
import { MySubscriptions } from './pages/portal/MySubscriptions';
import { MyInvoices } from './pages/portal/MyInvoices';
import { PaymentHistory } from './pages/portal/PaymentHistory';
import { CustomerProfilePage } from './pages/portal/CustomerProfile';
import { SubscriptionTimeline } from './pages/portal/SubscriptionTimeline';

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
];
