import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout, ToastProvider } from '@/shared/ui';
import { routes as p3Routes } from '@/modules/p3/routes';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <Router>
          <Layout>
            <Routes>
              {p3Routes.map((r, i) => (
                <Route key={i} path={r.path} element={r.element} />
              ))}
              <Route path="*" element={<Navigate to="/ui-demo" replace />} />
            </Routes>
          </Layout>
        </Router>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
