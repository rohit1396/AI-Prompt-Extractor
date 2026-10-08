import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, BrowserRouter, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router'
import './index.css'
import App from './App.tsx'
import { ImageProcessingPage } from './pages/ImageProcessingPage'
import { HistoryPage } from './pages/HistoryPage'
import { ResultPage } from './pages/ResultPage'
import { ExtractionSessionProvider, useExtractionSession } from './context/ExtractionSessionContext'
import { AuthProvider } from './context/AuthContext'
import { AuthGate } from './components/auth/AuthGate'

export function ImageProcessingEntry() {
  const navigate = useNavigate()
  const { session, resetSession } = useExtractionSession()

  useEffect(() => {
    if (session?.status === 'completed' && session.response?.id) {
      navigate(`/result/${session.response.id}`, { replace: true })
    }
  }, [navigate, session?.response?.id, session?.status])

  if (!session) {
    return <Navigate to="/" replace />
  }

  return (
    <ImageProcessingPage
      session={session}
      onChangeImage={() => {
        resetSession()
        navigate('/', { replace: true })
      }}
    />
  )
}

function LegacyHistoryResultRedirect() {
  const { extractionId } = useParams()
  const [searchParams] = useSearchParams()
  const page = searchParams.get('page')
  const query = page ? `?from=history&page=${page}` : '?from=history'
  return <Navigate to={`/result/${extractionId ?? ''}${query}`} replace />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <ExtractionSessionProvider>
        <BrowserRouter>
        <Routes>
          <Route path="/" element={<AuthGate><App /></AuthGate>} />
          <Route path="/imageprocessing" element={<AuthGate><ImageProcessingEntry /></AuthGate>} />
          <Route path="/imageprocessing/:extractionId" element={<AuthGate><ImageProcessingEntry /></AuthGate>} />
          <Route path="/result/:extractionId" element={<AuthGate><ResultPage /></AuthGate>} />
          <Route path="/history" element={<AuthGate><HistoryPage /></AuthGate>} />
          <Route path="/history/:extractionId" element={<LegacyHistoryResultRedirect />} />
        </Routes>
        </BrowserRouter>
      </ExtractionSessionProvider>
    </AuthProvider>
  </StrictMode>,
)
