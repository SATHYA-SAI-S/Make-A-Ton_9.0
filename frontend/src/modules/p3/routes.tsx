import React from 'react';
import { RouteObject } from 'react-router-dom';
import { UiDemo } from './pages/UiDemo';

export const routes: RouteObject[] = [
  {
    path: '/ui-demo',
    element: <UiDemo />,
  },
  {
    path: '/',
    element: <UiDemo />,
  },
];
