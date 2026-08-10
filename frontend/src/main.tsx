import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, BrowserRouter, Route, Routes, useNavigate } from 'react-router'
import './index.css'
import App from './App.tsx'
import { ImageProcessingPage } from './pages/ImageProcessingPage'
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
        </Routes>
      </BrowserRouter>
    </ExtractionSessionProvider>
  </StrictMode>,
)
