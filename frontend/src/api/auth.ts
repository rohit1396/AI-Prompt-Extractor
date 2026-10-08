const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type AuthUser = {
  id: number
  email: string
  first_name: string
  last_name: string
  display_name: string
}

type AuthResponse = { user: AuthUser }

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export async function ensureCsrfToken(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/csrf/`, { credentials: 'include' })
  const payload = (await response.json().catch(() => null)) as { csrfToken?: string } | null
  if (!response.ok || !payload?.csrfToken) throw new Error('Unable to initialize secure sign-in.')
  return payload.csrfToken
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me/`, { credentials: 'include' })
  if (response.status === 401 || response.status === 403) return null
  if (!response.ok) throw new Error('Unable to check your sign-in session.')
  return ((await response.json()) as AuthResponse).user
}

export async function signInWithGoogle(credential: string, csrfToken: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/google/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken') ?? csrfToken,
    },
    body: JSON.stringify({ credential }),
  })
  const payload = (await response.json().catch(() => null)) as AuthResponse & { detail?: string } | null
  if (!response.ok) throw new Error(payload?.detail ?? 'Google sign-in failed. Please try again.')
  return payload!.user
}

export async function signOut(csrfToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout/`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': getCookie('csrftoken') ?? csrfToken },
  })
  if (!response.ok && response.status !== 401) throw new Error('Unable to sign out.')
}
