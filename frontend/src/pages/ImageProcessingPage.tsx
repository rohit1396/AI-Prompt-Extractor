import { useEffect, useMemo } from 'react'
import type { ExtractionResponse } from '../api/extractions'
import { Navbar } from '../components/home/Navbar'

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`
  const mb = kb / 1024
  return `${mb.toFixed(mb < 10 ? 1 : 0)} MB`
}

export function ImageProcessingPage({
  file,
  uploadResponse,
  onChangeImage,
}: {
  file: File
  uploadResponse: ExtractionResponse
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
                Extracted prompt text
              </div>

              <div className="mt-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                {uploadResponse.message}
              </div>

              <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-950 px-4 py-4 text-sm leading-6 text-slate-100 whitespace-pre-wrap">
                {uploadResponse.extracted_text.trim() || 'No readable prompt text was detected in this image.'}
              </div>
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">OCR extraction completes as soon as the upload returns</p>
      </section>
    </main>
  )
}
