import { useState } from 'react'

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    if (!value) return
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return (
    <button
      type="button"
      onClick={() => void copy()}
      disabled={!value}
      className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function PromptCard({ title, text, emphasized = false }: { title: string; text: string; emphasized?: boolean }) {
  return (
    <div className={`rounded-2xl border px-4 py-4 ${emphasized ? 'border-blue-200 bg-blue-50/50' : 'border-slate-200 bg-white'}`}>
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</h3>
        <CopyButton value={text} />
      </div>
      <div className={`mt-3 whitespace-pre-wrap text-sm leading-6 ${emphasized ? 'text-slate-900' : 'text-slate-700'}`}>
        {text || 'No prompt text available.'}
      </div>
    </div>
  )
}

export function PromptComparison({
  extractedText,
  optimizedPrompt,
  template,
  components,
}: {
  extractedText: string
  optimizedPrompt?: string
  template?: string
  components?: Record<string, string[]>
}) {
  const componentEntries = Object.entries(components ?? {})

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Prompt comparison</h2>
          <p className="mt-2 text-sm text-slate-500">A deterministic rewrite built from the detected prompt components.</p>
        </div>
        {template ? <span className="w-fit rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold capitalize text-blue-700">{template} template</span> : null}
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <PromptCard title="Extracted prompt" text={extractedText} />
        <PromptCard title="Optimized prompt" text={optimizedPrompt ?? ''} emphasized />
      </div>

      {componentEntries.length > 0 ? (
        <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Detected components</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {componentEntries.map(([category, values]) => (
              <div key={category} className="rounded-xl bg-white px-3 py-2 text-sm">
                <span className="font-medium capitalize text-slate-500">{category.replace('_', ' ')}</span>
                <span className="ml-2 text-slate-800">{values.join(', ')}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}
