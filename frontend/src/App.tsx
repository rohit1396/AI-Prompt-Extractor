import { useNavigate } from 'react-router'
import { HomePage } from './pages/HomePage'

function App() {
  const navigate = useNavigate()

  const goToImageProcessing = (file: File) => {
    navigate('/imageprocessing', {
      state: { file },
    })
  }

  return <HomePage onProceed={goToImageProcessing} />
}

export default App
