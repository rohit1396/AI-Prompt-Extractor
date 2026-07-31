import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Navigate, BrowserRouter, Route, Routes, useLocation, useNavigate } from 'react-router'
import './index.css'
import App from './App.tsx'
import { ImageProcessingPage } from './pages/ImageProcessingPage'

type LocationState = {
  file?: File
}

export function ImageProcessingEntry() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null
  const file = state?.file

  if (!file) {
    return <Navigate to="/" replace />
  }

  return (
    <ImageProcessingPage
      file={file}
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
