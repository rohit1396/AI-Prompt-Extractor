import { HeroSection } from '../components/home/HeroSection'
import { HowItWorks } from '../components/home/HowItWorks'
import { Navbar } from '../components/home/Navbar'
import { UploadCard } from '../components/home/UploadCard'

export function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#f8fbff_0%,_#ffffff_38%,_#f8fafc_100%)] text-slate-700">
      <Navbar />
      <HeroSection />
      <UploadCard />
      <HowItWorks />
    </main>
  )
}
