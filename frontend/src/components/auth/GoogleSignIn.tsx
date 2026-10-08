import { useEffect, useRef } from 'react'
import { useAuth } from '../../context/AuthContext'

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (options: { client_id: string; callback: (response: { credential: string }) => void }) => void
          renderButton: (element: HTMLElement, options: { theme: string; size: string; width: number; text: string }) => void
        }
      }
    }
  }
}

const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

export function GoogleSignIn() {
  const buttonRef = useRef<HTMLDivElement>(null)
  const { authenticate, error } = useAuth()

  useEffect(() => {
    if (!clientId || !buttonRef.current) return
    const render = () => {
      if (!window.google || !buttonRef.current) return
      window.google.accounts.id.initialize({ client_id: clientId, callback: ({ credential }) => void authenticate(credential) })
      buttonRef.current.innerHTML = ''
      window.google.accounts.id.renderButton(buttonRef.current, { theme: 'outline', size: 'large', width: 320, text: 'signin_with' })
    }
    if (window.google) render()
    else {
      const script = document.createElement('script')
      script.src = 'https://accounts.google.com/gsi/client'
      script.async = true
      script.onload = render
      document.head.appendChild(script)
    }
  }, [authenticate])

  if (!clientId) return <p className="text-sm text-rose-600">Google sign-in is not configured yet.</p>
  return <div><div ref={buttonRef} className="min-h-10" />{error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}</div>
}
