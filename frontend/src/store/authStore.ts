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

const DEMO_AUTH_STORAGE_KEY = 'dbsherpa_demo_auth'
const DEMO_USER: AuthUser = {
  user_id: 'demo_user',
  email: 'demo@dbsherpa.local',
  name: 'Demo User',
  picture: null,
}

function readDemoAuthFlag(): boolean {
  try {
    return window.localStorage.getItem(DEMO_AUTH_STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

function persistDemoAuth(enabled: boolean): void {
  try {
    if (enabled) window.localStorage.setItem(DEMO_AUTH_STORAGE_KEY, '1')
    else window.localStorage.removeItem(DEMO_AUTH_STORAGE_KEY)
  } catch {
    /* noop: auth state still lives in-memory */
  }
}

interface AuthState {
  user: AuthUser | null
  /** `null` = not yet checked, `true` = checked + signed in, `false` = checked + signed out. */
  status: 'idle' | 'checking' | 'authenticated' | 'unauthenticated'
  setUser: (u: AuthUser | null) => void
  setStatus: (s: AuthState['status']) => void
  enableDemoUser: () => void
  /** Fetch /auth/me and update state. Returns `true` if signed in. */
  refresh: () => Promise<boolean>
  logout: () => Promise<void>
}

const API = '/api'

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: 'idle',
  setUser: (u) => {
    if (u?.user_id === DEMO_USER.user_id) persistDemoAuth(true)
    if (!u) persistDemoAuth(false)
    set({ user: u, status: u ? 'authenticated' : 'unauthenticated' })
  },
  setStatus: (s) => set({ status: s }),
  enableDemoUser: () => {
    persistDemoAuth(true)
    set({ user: DEMO_USER, status: 'authenticated' })
  },
  refresh: async () => {
    set({ status: 'checking' })
    if (readDemoAuthFlag()) {
      set({ user: DEMO_USER, status: 'authenticated' })
      return true
    }
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
    persistDemoAuth(false)
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
