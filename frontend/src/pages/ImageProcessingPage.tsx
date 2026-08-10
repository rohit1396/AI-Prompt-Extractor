import { useMemo } from 'react'
import type { ExtractionSession } from '../context/ExtractionSessionContext'
import { Navbar } from '../components/home/Navbar'

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(mb < 10 ? 1 : 0)} MB`
}

function ChecklistIcon({ status }: { status: ExtractionSession['checklist'][number]['status'] }) {
  if (status === 'done') {
    return (
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
        <span className="text-xs font-semibold">✓</span>
      </div>
    )
  }

  if (status === 'running') {
    return (
      <div className="flex h-6 w-6 items-center justify-center rounded-full border border-blue-200 bg-blue-50">
        <div className="h-3 w-3 animate-pulse rounded-full bg-blue-500" />
      </div>
    )
  }

  return <div className="h-6 w-6 rounded-full border border-slate-300 bg-white" />
}

export function ImageProcessingPage({
  session,
  onChangeImage,
}: {
  session: ExtractionSession
  onChangeImage: () => void
}) {
  const previewUrl = useMemo(() => session.previewUrl, [session.previewUrl])

  const isCompleted = session.status === 'completed' && session.response
  const extractedText = session.response?.extracted_text.trim()

  return (
    <main className="min-h-screen bg-[#fafafa] text-slate-700">
      <Navbar />

      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-8">
          <div className="rounded-[2rem] border border-slate-200 bg-white px-5 py-6 sm:px-6 sm:py-7">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 sm:w-[220px] sm:shrink-0">
                <img src={previewUrl} alt={session.file.name} className="h-56 w-full object-contain" />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex flex-col gap-4 pt-1 sm:pt-0">
                  <div>
                    <div className="text-lg font-semibold text-slate-950">{session.file.name}</div>
                    <div className="mt-1 text-sm text-slate-500">
                      {formatFileSize(session.file.size)} · {session.file.type.split('/')[1]?.toUpperCase() ?? 'IMAGE'} · Uploaded just now
                    </div>
                    <div className="mt-2 text-sm text-slate-600">
                      Backend response:{' '}
                      <span className="font-medium text-slate-900">
                        {session.status === 'error'
                          ? 'failed'
                          : session.status === 'completed'
                            ? session.response?.status
                            : 'processing'}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
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
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 sm:p-7">
            <div className="rounded-[1.25rem] border border-slate-200 bg-slate-50/80 p-6 sm:p-7">
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">
                {isCompleted ? 'Extracted prompt text' : 'Processing your image'}
              </div>

              {session.status === 'error' ? (
                <div className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
                  {session.error ?? 'Upload failed. Please try again.'}
                </div>
              ) : null}

              {isCompleted ? (
                <>
                  <div className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                    {session.response?.message}
                  </div>

                  <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-950 px-4 py-4 text-sm leading-6 whitespace-pre-wrap text-slate-100">
                    {extractedText || 'No readable prompt text was detected in this image.'}
                  </div>
                </>
              ) : (
                <>
                  <div className="mt-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                    Upload complete. OCR and prompt cleanup are still running.
                  </div>

                  <div className="mt-5 space-y-3">
                    {session.checklist.map((item) => (
                      <div key={item.key} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-3">
                        <div className="flex items-center gap-3">
                          <ChecklistIcon status={item.status} />
                          <span className="text-sm text-slate-700">{item.label}</span>
                        </div>
                        <span
                          className={[
                            'text-sm font-medium',
                            item.status === 'done'
                              ? 'text-emerald-600'
                              : item.status === 'running'
                                ? 'text-blue-600'
                                : 'text-slate-400',
                          ].join(' ')}
                        >
                          {item.status === 'done' ? 'Done' : item.status === 'running' ? 'Running...' : 'Waiting'}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-blue-600 transition-all duration-300"
                      style={{
                        width:
                          session.status === 'completed'
                            ? '100%'
                            : session.status === 'error'
                              ? '20%'
                              : '72%',
                      }}
                    />
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          {isCompleted ? 'Extraction completed successfully.' : 'This usually takes 5-10 seconds'}
        </p>
      </section>
    </main>
  )
}
