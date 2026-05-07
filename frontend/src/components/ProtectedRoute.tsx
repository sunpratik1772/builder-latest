/**
 * Auth-aware route gate.
 *
 * Three states matter:
 *   - `idle` / `checking` → show a thin loading splash, don't decide yet
 *   - `authenticated`     → render the wrapped tree
 *   - `unauthenticated`   → redirect to /login
 *
 * The `useAuthStore` hook is the single source of truth — same
 * value powers the avatar in the topbar.
 */
import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const status = useAuthStore((s) => s.status)
  const refresh = useAuthStore((s) => s.refresh)

  useEffect(() => {
    // CRITICAL: If returning from OAuth callback, skip the /me check.
    // AuthCallback will exchange the session_id and establish the
    // session first.
    if (window.location.hash?.includes('session_id=')) return
    if (status === 'idle') void refresh()
  }, [status, refresh])

  if (status === 'idle' || status === 'checking') {
    return (
      <div
        className="flex items-center justify-center min-h-screen"
        style={{ background: 'var(--bg-base)' }}
      >
        <Loader2 size={18} className="animate-spin" style={{ color: 'var(--text-2)' }} />
      </div>
    )
  }
  if (status === 'unauthenticated') return <Navigate to="/login" replace />
  return <>{children}</>
}
