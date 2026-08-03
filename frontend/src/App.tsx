import { useNavigate } from 'react-router'
import { uploadExtractionImage } from './api/extractions'
import { HomePage } from './pages/HomePage'

function App() {
  const navigate = useNavigate()

  const goToImageProcessing = async (file: File) => {
    const uploadResponse = await uploadExtractionImage(file)
    navigate('/imageprocessing', {
      state: { file, uploadResponse },
    })
    return uploadResponse
  }

  return <HomePage onProceed={goToImageProcessing} />
}

export default App
