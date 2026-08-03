import { useCallback, useEffect, useId, useMemo, useRef, useState, type ChangeEvent } from 'react'
import type { DummyUploadResponse } from '../../api/extractions'

type UploadState = 'empty' | 'selected' | 'uploading' | 'success' | 'error'

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

export function UploadCard({
  onProceed,
}: {
  onProceed: (file: File) => Promise<DummyUploadResponse>
}) {
  const inputId = useId()
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const timerRef = useRef<number | null>(null)
  const [state, setState] = useState<UploadState>('empty')
  const [isDragActive, setIsDragActive] = useState(false)
  const [selected, setSelected] = useState<SelectedFile | null>(null)
  const [successVisible, setSuccessVisible] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

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
    setErrorMessage(null)
    setState('empty')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [clearTimer, selected])

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) return
      if (selected) {
        URL.revokeObjectURL(selected.previewUrl)
      }
      const previewUrl = URL.createObjectURL(file)
      setSelected({ file, previewUrl })
      setSuccessVisible(false)
      setErrorMessage(null)
      setState('selected')
    },
    [selected],
  )

  const handleProceed = useCallback(async () => {
    if (!selected || state === 'uploading') return

    setState('uploading')
    setSuccessVisible(false)
    setErrorMessage(null)
    clearTimer()

    try {
      await onProceed(selected.file)
      setState('success')
      setSuccessVisible(true)
      clearTimer()
      timerRef.current = window.setTimeout(() => {
        setSuccessVisible(false)
      }, 3000)
    } catch (error) {
      setState('error')
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed. Please try again.')
    }
  }, [clearTimer, onProceed, selected, state])

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
            Image uploaded successfully. You can proceed to prompt extraction.
          </div>
        ) : null}

        {errorMessage ? (
          <div
            role="alert"
            className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            {errorMessage}
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
                        void handleProceed()
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
                Image uploaded successfully. You can proceed to prompt extraction.
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
                    void handleProceed()
                  }}
                >
                  Proceed to Extract Prompt
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
