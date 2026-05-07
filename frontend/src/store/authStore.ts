/**
 * Auth store + helpers.
 *
 * Single source of truth for the current user. The component tree
 * subscribes via `useAuthStore`; the imperative `loginWithGoogle()`
 * helper kicks off the Emergent OAuth dance; `logout()` calls the
 * backend and clears local state.
 *
 * The actual session-id-for-session-token exchange happens in
 * `AuthCallback` because it needs the URL fragment (which only
 * exists on the redirect bounce). Everything else just calls
 * `/api/auth/me` and trusts the cookie.
 */
import { create } from 'zustand'

export interface AuthUser {
  user_id: string
  email: string
  name: string
  picture?: string | null
}

interface AuthState {
  user: AuthUser | null
  /** `null` = not yet checked, `true` = checked + signed in, `false` = checked + signed out. */
  status: 'idle' | 'checking' | 'authenticated' | 'unauthenticated'
  setUser: (u: AuthUser | null) => void
  setStatus: (s: AuthState['status']) => void
  /** Fetch /auth/me and update state. Returns `true` if signed in. */
  refresh: () => Promise<boolean>
  logout: () => Promise<void>
}

const API = '/api'

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: 'idle',
  setUser: (u) =>
    set({ user: u, status: u ? 'authenticated' : 'unauthenticated' }),
  setStatus: (s) => set({ status: s }),
  refresh: async () => {
    set({ status: 'checking' })
    try {
      const r = await fetch(`${API}/auth/me`, { credentials: 'include' })
      if (!r.ok) throw new Error('not authed')
      const u: AuthUser = await r.json()
      set({ user: u, status: 'authenticated' })
      return true
    } catch {
      set({ user: null, status: 'unauthenticated' })
      return false
    }
  },
  logout: async () => {
    try {
      await fetch(`${API}/auth/logout`, { method: 'POST', credentials: 'include' })
    } catch {
      /* swallow — local state is what the UI cares about */
    }
    set({ user: null, status: 'unauthenticated' })
  },
}))

/**
 * Kick off Google OAuth via Emergent's hosted flow. After the user
 * accepts, the browser is redirected back to `${origin}/dashboard`
 * with `#session_id=…` in the fragment.
 *
 * REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
 */
export function loginWithGoogle(): void {
  const redirectUrl = window.location.origin + '/dashboard'
  window.location.href =
    'https://auth.emergentagent.com/?redirect=' + encodeURIComponent(redirectUrl)
}

/** "Pratik Singh" → "PS"; falls back to first letter of email. */
export function userInitials(u: AuthUser | null | undefined): string {
  if (!u) return '?'
  const name = (u.name || '').trim()
  if (name) {
    const parts = name.split(/\s+/).filter(Boolean)
    const a = parts[0]?.[0] ?? ''
    const b = parts.length > 1 ? parts[parts.length - 1][0] : ''
    return (a + b).toUpperCase().slice(0, 2)
  }
  return (u.email?.[0] ?? '?').toUpperCase()
}
