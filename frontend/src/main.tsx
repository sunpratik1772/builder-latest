/**
 * Vite entry point + top-level routing.
 *
 * Routes:
 *   /login        — public hero/sign-in page
 *   /dashboard    — main Studio (auth-gated). Also where the OAuth
 *                   callback lands; the URL fragment `#session_id=…`
 *                   is detected synchronously here so the
 *                   ProtectedRoute can't 401 against `/auth/me`
 *                   before the cookie is set.
 *   *             — anything else punts to /dashboard
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from 'react-router-dom'

import App from './App.tsx'
import LoginPage from './pages/LoginPage'
import AuthCallback from './pages/AuthCallback'
import DocsPage from './pages/docs/DocsPage'
import ProtectedRoute from './components/ProtectedRoute'
import './styles/linear-tokens.css'
import './styles/globals.css'
import './styles/agent-animations.css'

function AppRouter() {
  const location = useLocation()
  // Synchronous check (NOT in useEffect) — we have to win the race
  // against ProtectedRoute's `/auth/me` call.
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />
  }
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/docs" element={<DocsPage />} />
      <Route path="/docs/:section/:item" element={<DocsPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <App />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  </React.StrictMode>,
)
