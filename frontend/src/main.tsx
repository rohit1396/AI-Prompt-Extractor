import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, BrowserRouter, Route, Routes, useNavigate } from 'react-router'
import './index.css'
import App from './App.tsx'
import { ImageProcessingPage } from './pages/ImageProcessingPage'
import { HistoryPage } from './pages/HistoryPage'
import { ExtractionDetailPage } from './pages/ExtractionDetailPage'
import { ExtractionSessionProvider, useExtractionSession } from './context/ExtractionSessionContext'

export function ImageProcessingEntry() {
  const navigate = useNavigate()
  const { session, resetSession } = useExtractionSession()

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
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/history/:extractionId" element={<ExtractionDetailPage />} />
        </Routes>
      </BrowserRouter>
    </ExtractionSessionProvider>
  </StrictMode>,
)
