import { StepCard } from './StepCard'

export function HowItWorks() {
  return (
    <section className="mx-auto max-w-6xl px-4 pb-14 sm:px-6 lg:px-8">
      <div className="mb-5">
        <h2 className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
          How PromptLens Works
        </h2>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <StepCard
          number="01"
          title="Upload Screenshot"
          description="Upload any screenshot containing an AI prompt."
        />
        <StepCard
          number="02"
          title="OCR Extraction"
          description="PromptLens extracts the text using PaddleOCR."
        />
        <StepCard
          number="03"
          title="Copy Prompt"
          description="Review and copy the cleaned prompt."
        />
      </div>
    </section>
  )
}
