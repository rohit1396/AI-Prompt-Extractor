import { useLocation } from 'react-router'
import type { ReactNode } from 'react'
import { GoogleSignIn } from './GoogleSignIn'
import { useAuth } from '../../context/AuthContext'

export function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="min-h-screen grid place-items-center text-sm text-slate-500">Checking your sign-in...</div>
  if (user) return <>{children}</>
  return (
    <main className="min-h-screen grid place-items-center bg-slate-50 px-6">
      <section className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-white">P</div>
        <h1 className="mt-6 text-2xl font-semibold text-slate-950">Sign in to PromptLens</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">Sign in with Google to extract prompts and keep your private history.</p>
        <div className="mt-7 flex justify-center"><GoogleSignIn /></div>
        <p className="mt-5 text-xs text-slate-400">You were trying to open {location.pathname}</p>
      </section>
    </main>
  )
}
