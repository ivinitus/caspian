import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { preventFormNavigation } from './utils/navigation'
import './index.css'
import App from './App.jsx'

// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error caught:', event.error);
  // Prevent the error from causing page blanking
  event.preventDefault();
});

// Prevent unhandled promise rejections from breaking the app
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // Prevent the rejection from causing page blanking
  event.preventDefault();
});

// Prevent form submission navigation
document.addEventListener('submit', function(e) {
  console.log('Prevented form submission navigation');
  return preventFormNavigation(e);
}, true);

// Add an extra defensive measure against page reloads
window.addEventListener('beforeunload', function(e) {
  // Only show confirmation dialog during active chat (not during page refresh)
  const isActiveChat = document.querySelector('.message-input:not([disabled])');
  if (isActiveChat) {
    e.preventDefault();
    e.returnValue = '';
    return '';
  }
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
