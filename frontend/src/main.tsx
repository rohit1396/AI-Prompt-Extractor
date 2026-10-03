import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, BrowserRouter, Route, Routes, useNavigate } from 'react-router'
import './index.css'
import App from './App.tsx'
import { ImageProcessingPage } from './pages/ImageProcessingPage'
import { HistoryPage } from './pages/HistoryPage'
import { ExtractionDetailPage } from './pages/ExtractionDetailPage'
import { ResultPage } from './pages/ResultPage'
import { ExtractionSessionProvider, useExtractionSession } from './context/ExtractionSessionContext'

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

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ExtractionSessionProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/imageprocessing" element={<ImageProcessingEntry />} />
          <Route path="/imageprocessing/:extractionId" element={<ImageProcessingEntry />} />
          <Route path="/result/:extractionId" element={<ResultPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:extractionId" element={<ExtractionDetailPage />} />
        </Routes>
      </BrowserRouter>
    </ExtractionSessionProvider>
  </StrictMode>,
)
