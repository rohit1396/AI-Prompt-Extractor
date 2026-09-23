import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { Navbar } from '../components/home/Navbar'
import { fetchExtraction, type ExtractionRecord } from '../api/extractions'

const POLL_INTERVAL_MS = 2000

function formatDate(value?: string) {
  if (!value) return 'Unknown time'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatFileSize(bytes = 0) {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

function classificationLabel(label?: string) {
  if (label === 'prompt') return 'Prompt-like'
  if (label === 'not_prompt') return 'Not prompt-like'
  if (label === 'uncertain') return 'Uncertain'
  return 'Not classified'
}

function classificationStyle(label?: string) {
  if (label === 'prompt') return 'bg-emerald-100 text-emerald-700'
  if (label === 'not_prompt') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-600'
}

function DetailStatus({ record }: { record: ExtractionRecord }) {
  const active = record.status === 'received' || record.status === 'queued' || record.status === 'processing'
  return (
    <div className={`rounded-2xl px-4 py-3 text-sm ${record.status === 'failed' ? 'border border-rose-200 bg-rose-50 text-rose-800' : 'border border-slate-200 bg-slate-50 text-slate-700'}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${record.status === 'failed' ? 'bg-rose-100 text-rose-700' : 'bg-blue-100 text-blue-700'}`}>
          {record.status}
        </span>
        {active ? <span>Processing is still in progress. This page will update automatically.</span> : <span>{record.message}</span>}
      </div>
      {record.error_message ? <div className="mt-2 text-sm">{record.error_message}</div> : null}
    </div>
  )
}

export function ExtractionDetailPage() {
  const { extractionId } = useParams()
  const [searchParams] = useSearchParams()
  const historyPage = Number(searchParams.get('page')) > 1 ? searchParams.get('page') : null
  const historyUrl = historyPage ? `/history?page=${historyPage}` : '/history'
  const [record, setRecord] = useState<ExtractionRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    let timer: number | null = null

    const load = async () => {
      if (!extractionId) {
        setError('No extraction record was specified.')
        setLoading(false)
        return
      }

      try {
        const latest = await fetchExtraction(extractionId)
        if (cancelled) return
        setRecord(latest)
        setLoading(false)

        if (latest.status !== 'completed' && latest.status !== 'failed') {
          timer = window.setTimeout(load, POLL_INTERVAL_MS)
        }
      } catch (requestError) {
        if (cancelled) return
        setError(requestError instanceof Error ? requestError.message : 'Unable to load this extraction.')
        setLoading(false)
      }
    }

    // This effect synchronizes the page with the detail API and its polling lifecycle.
    void load()
    return () => {
      cancelled = true
      if (timer !== null) window.clearTimeout(timer)
    }
  }, [extractionId])

  const positiveSignals = record?.matched_signals?.filter((signal) => signal.polarity === 'positive') ?? []
  const negativeSignals = record?.matched_signals?.filter((signal) => signal.polarity === 'negative') ?? []
  const displayText = record?.extracted_text?.trim() || record?.raw_ocr_text?.trim() || 'No readable OCR text was detected in this image.'

  return (
    <main className="min-h-screen bg-[#fafafa] text-slate-700">
      <Navbar />
      <section className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <Link to={historyUrl} className="text-sm font-medium text-blue-600 hover:text-blue-800">← Back to history</Link>
        <div className="mt-5">
          {loading ? <div className="rounded-2xl border border-slate-200 bg-white px-5 py-16 text-center text-sm text-slate-500">Loading extraction...</div> : null}
          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-5 text-sm text-rose-800">
              <div className="font-medium">Unable to load extraction</div>
              <div className="mt-1">{error}</div>
            </div>
          ) : null}
          {!loading && !error && record ? (
            <div className="space-y-5">
              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 sm:p-6">
                <div className="flex flex-col gap-5 sm:flex-row">
                  <div className="h-56 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 sm:w-64 sm:shrink-0">
                    {record.image_url ? <img src={record.image_url} alt={record.filename} className="h-full w-full object-contain" /> : <div className="flex h-full items-center justify-center text-sm text-slate-400">No preview available</div>}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h1 className="break-all text-2xl font-semibold text-slate-950">{record.filename}</h1>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${classificationStyle(record.classification_label)}`}>{classificationLabel(record.classification_label)}</span>
                    </div>
                    <div className="mt-2 text-sm text-slate-500">{formatFileSize(record.file_size)} · {record.content_type} · Created {formatDate(record.created_at)}</div>
                    <div className="mt-5"><DetailStatus record={record} /></div>
                    <dl className="mt-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                      <div><dt className="text-slate-400">Score</dt><dd className="mt-1 font-semibold text-slate-900">{record.classification_score ?? '—'}</dd></div>
                      <div><dt className="text-slate-400">Confidence</dt><dd className="mt-1 font-semibold text-slate-900">{record.classification_confidence == null ? '—' : `${record.classification_confidence}%`}</dd></div>
                      <div><dt className="text-slate-400">Processing</dt><dd className="mt-1 font-semibold text-slate-900">{record.processing_time_ms == null ? '—' : `${record.processing_time_ms} ms`}</dd></div>
                      <div><dt className="text-slate-400">Updated</dt><dd className="mt-1 font-semibold text-slate-900">{formatDate(record.updated_at)}</dd></div>
                    </dl>
                  </div>
                </div>
              </div>

              <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
                <h2 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Extracted OCR text</h2>
                <div className="mt-3 whitespace-pre-wrap rounded-2xl bg-slate-950 px-4 py-4 text-sm leading-6 text-slate-100">{displayText}</div>
              </section>

              <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
                <h2 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Matched signals</h2>
                {positiveSignals.length === 0 && negativeSignals.length === 0 ? <p className="mt-3 text-sm text-slate-500">No weighted signals were matched.</p> : (
                  <div className="mt-4 grid gap-5 md:grid-cols-2">
                    {[['Positive signals', positiveSignals, 'emerald'], ['Negative signals', negativeSignals, 'rose']].map(([title, signals, tone]) => (
                      <div key={title as string}>
                        <h3 className={`text-sm font-semibold ${tone === 'emerald' ? 'text-emerald-700' : 'text-rose-700'}`}>{title as string}</h3>
                        <div className="mt-2 space-y-2">
                          {(signals as NonNullable<ExtractionRecord['matched_signals']>).map((signal) => (
                            <div key={`${signal.polarity}-${signal.text}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                              <span className="min-w-0 truncate text-slate-700">{signal.text} <span className="text-xs text-slate-400">· {signal.category}</span></span>
                              <span className="shrink-0 font-semibold text-slate-700">{signal.weight > 0 ? '+' : ''}{signal.weight}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  )
}
