import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router'
import './index.css'
import App from './App.tsx'
import { ImageProcessingPage } from './pages/ImageProcessingPage'
import type { ExtractionResponse } from './api/extractions'

type LocationState = {
  file?: File
  uploadResponse?: ExtractionResponse
}

export function ImageProcessingEntry() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null
  const file = state?.file
  const uploadResponse = state?.uploadResponse

  if (!file || !uploadResponse) {
    return <Navigate to="/" replace />
  }

  return (
    <ImageProcessingPage
      file={file}
      uploadResponse={uploadResponse}
      onChangeImage={() => {
        navigate('/', { replace: true })
      }}
    />
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/imageprocessing" element={<ImageProcessingEntry />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
