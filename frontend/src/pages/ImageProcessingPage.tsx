import { useEffect, useMemo } from 'react'
import type { DummyUploadResponse } from '../api/extractions'
import { Navbar } from '../components/home/Navbar'

type StepState = 'waiting' | 'running' | 'done'

type ProcessingStep = {
  id: string
  label: string
  status: StepState
}

const STEPS: ProcessingStep[] = [
  { id: 'storage', label: 'Image uploaded to storage', status: 'done' },
  { id: 'preprocess', label: 'Image preprocessed', status: 'done' },
  { id: 'ocr', label: 'Text extracted via OCR', status: 'done' },
  { id: 'classification', label: 'AI classifying & cleaning prompt', status: 'running' },
  { id: 'optimization', label: 'Optimizing prompt', status: 'waiting' },
]

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(mb < 10 ? 1 : 0)} MB`
}

function Spinner() {
  return (
    <svg
      className="h-5 w-5 animate-spin text-blue-600"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.2" strokeWidth="2.5" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function StepStatus({ status }: { status: StepState }) {
  if (status === 'done') {
    return <span className="h-6 w-6 rounded-full bg-emerald-200 ring-8 ring-emerald-100" />
  }

  if (status === 'running') {
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-600">
        <Spinner />
      </span>
    )
  }

  return <span className="h-6 w-6 rounded-full border border-slate-200 bg-white" />
}

function StepRow({ step }: { step: ProcessingStep }) {
  return (
    <div className="flex items-center gap-3 sm:gap-4">
      <StepStatus status={step.status} />
      <div className="min-w-0 flex-1 text-sm text-slate-700">{step.label}</div>
      <div
        className={[
          'text-sm font-medium',
          step.status === 'done'
            ? 'text-emerald-700'
            : step.status === 'running'
              ? 'text-blue-600'
              : 'text-slate-400',
        ].join(' ')}
      >
        {step.status === 'done' ? 'Done' : step.status === 'running' ? 'Running...' : 'Waiting'}
      </div>
    </div>
  )
}

export function ImageProcessingPage({
  file,
  uploadResponse,
  onChangeImage,
}: {
  file: File
  uploadResponse: DummyUploadResponse
  onChangeImage: () => void
}) {
  const previewUrl = useMemo(() => URL.createObjectURL(file), [file])

  useEffect(() => {
    return () => {
      URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  return (
    <main className="min-h-screen bg-[#fafafa] text-slate-700">
      <Navbar />

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-8">
          <div className="rounded-[2rem] border border-slate-200 bg-white px-5 py-6 sm:px-6 sm:py-7">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 sm:w-[220px] sm:shrink-0">
                <img src={previewUrl} alt={file.name} className="h-56 w-full object-contain" />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex flex-col gap-4 pt-1 sm:pt-0">
                  <div>
                    <div className="text-lg font-semibold text-slate-950">{file.name}</div>
                    <div className="mt-1 text-sm text-slate-500">
                      {formatFileSize(file.size)} · {file.type.split('/')[1]?.toUpperCase() ?? 'IMAGE'} ·
                      Uploaded just now
                    </div>
                    <div className="mt-2 text-sm text-slate-600">
                      Backend response: <span className="font-medium text-slate-900">{uploadResponse.status}</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="inline-flex w-fit items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                    onClick={onChangeImage}
                  >
                    Change image
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 sm:p-7">
            <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50/80 p-6 sm:p-7">
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                Processing your image
              </div>

              <div className="mt-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                {uploadResponse.message}
              </div>

              <div className="mt-6 space-y-5">
                {STEPS.map((step) => (
                  <StepRow key={step.id} step={step} />
                ))}
              </div>

              <div className="mt-7 h-1.5 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full w-[60%] rounded-full bg-blue-600" />
              </div>
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">This usually takes 5–10 seconds</p>
      </section>
    </main>
  )
}
