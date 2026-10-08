/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { ensureCsrfToken, fetchCurrentUser, signInWithGoogle, signOut, type AuthUser } from '../api/auth'
import { captureFrontendException, Sentry } from '../observability'

type AuthContextValue = {
  user: AuthUser | null
  loading: boolean
  error: string | null
  csrfToken: string
  authenticate: (credential: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [csrfToken, setCsrfToken] = useState('')

  useEffect(() => {
    Promise.all([ensureCsrfToken(), fetchCurrentUser()])
      .then(([token, currentUser]) => {
        setCsrfToken(token)
        setUser(currentUser)
      })
      .catch((requestError: unknown) => {
        captureFrontendException(requestError, 'authentication_initialization')
        setError(requestError instanceof Error ? requestError.message : 'Unable to initialize authentication.')
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (user) {
      Sentry.setUser({ id: String(user.id), email: user.email })
    } else {
      Sentry.setUser(null)
    }
  }, [user])

  const authenticate = useCallback(async (credential: string) => {
    setError(null)
    try {
      setUser(await signInWithGoogle(credential, csrfToken))
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : 'Google sign-in failed.'
      captureFrontendException(requestError, 'authentication')
      setError(message)
      throw requestError
    }
  }, [csrfToken])

  const logout = useCallback(async () => {
    await signOut(csrfToken)
    setUser(null)
  }, [csrfToken])

  const value = useMemo(() => ({ user, loading, error, csrfToken, authenticate, logout }), [user, loading, error, csrfToken, authenticate, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
