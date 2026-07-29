import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
} from 'react'

type UploadState = 'empty' | 'selected' | 'uploading' | 'success'

type SelectedFile = {
  file: File
  previewUrl: string
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(mb < 10 ? 1 : 0)} MB`
}

function NavIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true">
      <path
        d="M7 7.5C7 6.12 8.12 5 9.5 5h5C15.88 5 17 6.12 17 7.5v5c0 1.38-1.12 2.5-2.5 2.5h-5C8.12 15 7 13.88 7 12.5v-5Z"
        stroke="currentColor"
        strokeWidth="1.7"
      />
      <path d="M9 18h6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

function UploadGlyph() {
  return (
    <svg viewBox="0 0 24 24" className="h-10 w-10 text-blue-500" fill="none" aria-hidden="true">
      <path
        d="M12 16V8m0 0-3 3m3-3 3 3"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M5 16.5A4.5 4.5 0 0 1 9.5 12h1.1a4.4 4.4 0 0 1 8.4 1.4A3.9 3.9 0 0 1 17 21H8.5A3.5 3.5 0 0 1 5 17.5v-1Z"
        stroke="currentColor"
        strokeWidth="1.4"
      />
    </svg>
  )
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

function StepCard({
  number,
  title,
  description,
}: {
  number: string
  title: string
  description: string
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="text-xs font-medium tracking-[0.24em] text-slate-400">{number}</div>
      <h3 className="mt-8 text-base font-medium text-slate-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </article>
  )
}

function Badge({ children }: { children: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
      {children}
    </span>
  )
}

function Navbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
            <NavIcon className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="text-[15px] font-semibold text-slate-950">PromptLens</div>
            <div className="text-xs text-slate-500">Screenshot prompt extraction</div>
          </div>
        </div>

        <nav className="flex items-center gap-2 text-sm">
          <a
            href="#extract"
            className="rounded-full bg-blue-50 px-4 py-2 font-medium text-blue-700 transition hover:bg-blue-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            Extract
          </a>
          <span
            aria-disabled="true"
            className="rounded-full px-4 py-2 font-medium text-slate-400"
          >
            History
          </span>
        </nav>
      </div>
    </header>
  )
}

function HeroSection() {
  return (
    <section className="mx-auto max-w-3xl px-4 pt-12 text-center sm:px-6 lg:pt-14">
      <div className="flex justify-center">
        <Badge>Powered by PaddleOCR</Badge>
      </div>
      <h1 className="mt-5 text-balance text-4xl font-semibold tracking-[-0.05em] text-slate-950 sm:text-5xl lg:text-6xl">
        Extract AI prompts from screenshots
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-pretty text-base leading-7 text-slate-600 sm:text-lg">
        Upload screenshots from Instagram, Midjourney, ChatGPT, X, Reddit or anywhere else.
        PromptLens automatically extracts and cleans AI prompts.
      </p>
    </section>
  )
}

function UploadCard() {
  const inputId = useId()
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const timerRef = useRef<number | null>(null)
  const [state, setState] = useState<UploadState>('empty')
  const [isDragActive, setIsDragActive] = useState(false)
  const [selected, setSelected] = useState<SelectedFile | null>(null)
  const [successVisible, setSuccessVisible] = useState(false)

  const supportedFormats = useMemo(() => ['PNG', 'JPG', 'JPEG', 'WEBP'], [])

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  const resetSelection = useCallback(() => {
    clearTimer()
    if (selected) {
      URL.revokeObjectURL(selected.previewUrl)
    }
    setSelected(null)
    setSuccessVisible(false)
    setState('empty')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [clearTimer, selected])

  const startUpload = useCallback(() => {
    if (!selected || state === 'uploading') return
    setSuccessVisible(false)
    setState('uploading')
    clearTimer()
    timerRef.current = window.setTimeout(() => {
      setState('success')
      setSuccessVisible(true)
      timerRef.current = window.setTimeout(() => {
        setSuccessVisible(false)
      }, 3000)
      }, 1600)
  }, [clearTimer, selected, state])

  const handleFile = useCallback((file: File | null) => {
    if (!file) return
    if (selected) {
      URL.revokeObjectURL(selected.previewUrl)
    }
    const previewUrl = URL.createObjectURL(file)
    setSelected({ file, previewUrl })
    setSuccessVisible(false)
    setState('selected')
  }, [selected])

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0] ?? null)
  }

  useEffect(() => {
    const onPaste = (event: ClipboardEvent) => {
      const pasted = Array.from(event.clipboardData?.files ?? []).find((file) =>
        file.type.startsWith('image/'),
      )
      if (pasted) {
        handleFile(pasted)
      }
    }

    window.addEventListener('paste', onPaste)
    return () => {
      window.removeEventListener('paste', onPaste)
      clearTimer()
    }
  }, [clearTimer, handleFile])

  useEffect(() => {
    return () => {
      if (selected) {
        URL.revokeObjectURL(selected.previewUrl)
      }
    }
  }, [selected])

  return (
    <section id="extract" className="mx-auto max-w-5xl px-4 pb-8 pt-10 sm:px-6 lg:pb-12">
      <div className="rounded-[2rem] border border-slate-200 bg-white/95 p-4 shadow-[0_20px_60px_rgba(15,23,42,0.08)] sm:p-6">
        {successVisible ? (
          <div
            role="status"
            aria-live="polite"
            className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          >
            Image uploaded successfully. The OCR functionality will be implemented later.
          </div>
        ) : null}

        <div
          onDragOver={(event) => {
            event.preventDefault()
            if (state !== 'uploading') setIsDragActive(true)
          }}
          onDragLeave={() => setIsDragActive(false)}
          onDrop={(event) => {
            event.preventDefault()
            setIsDragActive(false)
            if (state === 'uploading') return
            handleFile(event.dataTransfer.files?.[0] ?? null)
          }}
          className={[
            'rounded-[1.75rem] border border-dashed p-5 text-center transition duration-200 sm:p-8',
            state === 'uploading' ? 'cursor-not-allowed bg-slate-50 opacity-95' : 'cursor-pointer bg-slate-50/80',
            isDragActive ? 'border-blue-400 bg-blue-50 shadow-[0_0_0_4px_rgba(59,130,246,0.08)]' : 'border-slate-200',
          ].join(' ')}
          role="button"
          tabIndex={0}
          aria-label="Upload screenshot"
          aria-disabled={state === 'uploading'}
          onKeyDown={(event) => {
            if (state === 'uploading') return
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault()
              fileInputRef.current?.click()
            }
          }}
          onClick={() => {
            if (state !== 'uploading') fileInputRef.current?.click()
          }}
        >
          {state === 'empty' ? (
            <div className="mx-auto flex max-w-xl flex-col items-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 shadow-inner shadow-blue-200/60">
                <UploadGlyph />
              </div>
              <h2 className="mt-5 text-lg font-semibold text-slate-950">Drop your screenshot here</h2>
              <p className="mt-2 text-sm text-slate-600">
                Drag and drop, or click to browse from your device
              </p>

              <div className="mt-5 flex flex-col items-center gap-3">
                <button
                  type="button"
                  className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  onClick={(event) => {
                    event.stopPropagation()
                    fileInputRef.current?.click()
                  }}
                >
                  Browse files
                  <span className="ml-2 text-sm">↗</span>
                </button>
                <div className="text-xs text-slate-500">or paste from clipboard</div>
                <div className="flex flex-wrap justify-center gap-2">
                  {supportedFormats.map((item) => (
                    <span
                      key={item}
                      className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-500"
                    >
                      {item}
                    </span>
                  ))}
                  <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-500">
                    Max 10MB
                  </span>
                </div>
              </div>
            </div>
          ) : null}

          {state === 'selected' && selected ? (
            <div className="mx-auto flex max-w-2xl flex-col items-center gap-5">
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <img
                  src={selected.previewUrl}
                  alt={selected.file.name}
                  className="max-h-[320px] w-full object-contain"
                />
              </div>
              <div className="w-full rounded-2xl bg-white p-4 shadow-sm">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="text-left">
                    <div className="text-sm font-medium text-slate-950">{selected.file.name}</div>
                    <div className="mt-1 text-sm text-slate-500">{formatFileSize(selected.file.size)}</div>
                  </div>
                  <div className="flex flex-wrap items-center justify-center gap-3">
                    <button
                      type="button"
                      className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      onClick={(event) => {
                        event.stopPropagation()
                        resetSelection()
                      }}
                    >
                      Remove image
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                      onClick={(event) => {
                        event.stopPropagation()
                        startUpload()
                      }}
                    >
                      Upload screenshot
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {state === 'uploading' ? (
            <div className="mx-auto flex min-h-[360px] max-w-xl flex-col items-center justify-center gap-4">
              <Spinner />
              <div className="text-base font-medium text-slate-950">Uploading...</div>
              <p className="text-sm text-slate-500">Please keep this tab open while the screenshot is processed.</p>
            </div>
          ) : null}

          {state === 'success' && selected ? (
            <div className="mx-auto flex max-w-2xl flex-col items-center gap-5">
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <img
                  src={selected.previewUrl}
                  alt={selected.file.name}
                  className="max-h-[320px] w-full object-contain opacity-95"
                />
              </div>
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                Image uploaded successfully. The OCR functionality will be implemented later.
              </div>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  type="button"
                  className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  onClick={(event) => {
                    event.stopPropagation()
                    resetSelection()
                  }}
                >
                  Remove image
                </button>
                <button
                  type="button"
                  className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  onClick={(event) => {
                    event.stopPropagation()
                    startUpload()
                  }}
                >
                  Upload again
                </button>
              </div>
            </div>
          ) : null}
        </div>

        <p className="mt-4 text-center text-sm text-slate-500">Press Ctrl+V anywhere on this page to paste a screenshot</p>
      </div>

      <input
        ref={fileInputRef}
        id={inputId}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        className="sr-only"
        onChange={handleInputChange}
      />
    </section>
  )
}

function HowItWorks() {
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
