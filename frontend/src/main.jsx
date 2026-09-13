import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import { I18nProvider } from './i18n'
import { syncPendingReports } from './lib/offlineStore'
import './index.css'
import './styles/v2.css'

// Send outbreak reports that were saved while offline.
const sync = () => syncPendingReports().catch(() => {})
window.addEventListener('online', sync)
sync()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <I18nProvider>
      <BrowserRouter>
        <App />
        <Toaster position="top-center" toastOptions={{ duration: 4000, style: { fontFamily: 'Inter, sans-serif', fontSize: '0.9rem' } }} />
      </BrowserRouter>
    </I18nProvider>
  </React.StrictMode>,
)
