import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { Navbar } from '../components/home/Navbar'
import { fetchExtractionHistory, type ExtractionHistoryPage, type ExtractionRecord } from '../api/extractions'

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

function statusStyle(status: string) {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'failed') return 'bg-rose-100 text-rose-700'
  return 'bg-blue-100 text-blue-700'
}

function classificationStyle(label?: string) {
  if (label === 'prompt') return 'bg-emerald-50 text-emerald-700'
  if (label === 'not_prompt') return 'bg-amber-50 text-amber-700'
  return 'bg-slate-100 text-slate-600'
}

function classificationText(record: ExtractionRecord) {
  if (record.classification_label === 'prompt') return 'Prompt-like'
  if (record.classification_label === 'not_prompt') return 'Not prompt-like'
  if (record.classification_label === 'uncertain') return 'Uncertain'
  return 'Not classified'
}

function HistoryCard({ record, page }: { record: ExtractionRecord; page: number }) {
  return (
    <Link to={`/history/${record.id}?page=${page}`} className="block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
      <article className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-blue-300 hover:shadow-md sm:flex-row sm:items-center">
      <div className="h-20 w-20 shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
        {record.image_url ? (
          <img src={record.image_url} alt={record.filename} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-slate-400">No preview</div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="truncate font-semibold text-slate-950">{record.filename}</h2>
          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyle(record.status)}`}>
            {record.status}
          </span>
        </div>
        <div className="mt-1 text-sm text-slate-500">
          {formatDate(record.created_at)} · {formatFileSize(record.file_size)}
        </div>
        {record.status === 'failed' && record.error_message ? (
          <p className="mt-2 text-sm text-rose-700">{record.error_message}</p>
        ) : null}
      </div>
      <div className="flex shrink-0 flex-col items-start gap-2 sm:items-end">
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${classificationStyle(record.classification_label)}`}>
          {classificationText(record)}
        </span>
        {typeof record.classification_score === 'number' || typeof record.classification_confidence === 'number' ? (
          <span className="text-xs text-slate-500">
            {typeof record.classification_score === 'number' ? `Score ${record.classification_score}` : ''}
            {typeof record.classification_score === 'number' && typeof record.classification_confidence === 'number' ? ' · ' : ''}
            {typeof record.classification_confidence === 'number' ? `${record.classification_confidence}% confidence` : ''}
          </span>
        ) : null}
      </div>
      </article>
    </Link>
  )
}

export function HistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [history, setHistory] = useState<ExtractionHistoryPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const parsedPage = Number(searchParams.get('page'))
  const page = Number.isInteger(parsedPage) && parsedPage > 0 ? parsedPage : 1

  const loadHistory = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setHistory(await fetchExtractionHistory(page))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load extraction history.')
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    // The request is the external system this effect synchronizes with.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadHistory()
  }, [loadHistory])

  const goToPage = (nextPage: number) => {
    setSearchParams(nextPage === 1 ? {} : { page: String(nextPage) })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <main className="min-h-screen bg-[#fafafa] text-slate-700">
      <Navbar />
      <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-600">Workspace</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Extraction history</h1>
            <p className="mt-2 text-sm text-slate-500">Review every image processed by PromptLens.</p>
          </div>
          {history ? <div className="text-sm text-slate-500">{history.count} total extraction{history.count === 1 ? '' : 's'}</div> : null}
        </div>

        {loading ? <div className="rounded-2xl border border-slate-200 bg-white px-5 py-12 text-center text-sm text-slate-500">Loading extraction history...</div> : null}
        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-800">
            <div>{error}</div>
            <button type="button" onClick={() => void loadHistory()} className="mt-3 rounded-lg bg-white px-3 py-2 text-sm font-medium text-rose-700 ring-1 ring-rose-200 hover:bg-rose-100">
              Try again
            </button>
          </div>
        ) : null}
        {!loading && !error && history?.results.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-16 text-center">
            <h2 className="font-semibold text-slate-900">No extractions yet</h2>
            <p className="mt-2 text-sm text-slate-500">Upload an image to create your first history record.</p>
          </div>
        ) : null}
        {!loading && !error && history && history.results.length > 0 ? (
          <>
            <div className="space-y-3">
              {history.results.map((record) => <HistoryCard key={record.id} record={record} page={page} />)}
            </div>
            <div className="mt-6 flex items-center justify-between">
              <button type="button" disabled={!history.previous} onClick={() => goToPage(page - 1)} className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
                Previous
              </button>
              <span className="text-sm text-slate-500">Page {page}</span>
              <button type="button" disabled={!history.next} onClick={() => goToPage(page + 1)} className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
                Next
              </button>
            </div>
          </>
        ) : null}
      </section>
    </main>
  )
}
