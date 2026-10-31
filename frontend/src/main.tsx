import React from 'react';
import ReactDOM from 'react-dom/client';
import { BillingModule } from './modules/p2';

const rootEl = document.getElementById('root');
if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <BillingModule />
    </React.StrictMode>
  );
}
