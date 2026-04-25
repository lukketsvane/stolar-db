import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './index.css';

if ('serviceWorker' in navigator) {
  const params = new URLSearchParams(window.location.search);
  const killSw = params.has('nosw') || params.has('reset');
  window.addEventListener('load', () => {
    if (killSw) {
      navigator.serviceWorker.getRegistrations().then((regs) => {
        regs.forEach((r) => r.unregister());
        if (window.caches) caches.keys().then((keys) => keys.forEach((k) => caches.delete(k)));
        console.log('[sw] unregistered + caches cleared');
      });
    } else {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.warn('SW registration failed:', err);
      });
    }
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
