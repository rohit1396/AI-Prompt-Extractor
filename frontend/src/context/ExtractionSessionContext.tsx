/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import type { ExtractionRecord } from '../api/extractions'
import { fetchExtraction, uploadExtractionImage } from '../api/extractions'

export type ChecklistItem = {
  key: 'received' | 'queued' | 'processing'
  label: string
  status: 'pending' | 'running' | 'done'
}

export type ExtractionSession = {
  file: File
  previewUrl: string
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed' | 'error'
  response: ExtractionRecord | null
  error: string | null
  checklist: ChecklistItem[]
}

type ExtractionSessionContextValue = {
  session: ExtractionSession | null
  startExtraction: (file: File) => void
  resetSession: () => void
}

const ExtractionSessionContext = createContext<ExtractionSessionContextValue | null>(null)

const CHECKLIST_TEMPLATE: Omit<ChecklistItem, 'status'>[] = [
  { key: 'received', label: 'Image received' },
  { key: 'queued', label: 'OCR job queued' },
  { key: 'processing', label: 'OCR extraction in progress' },
]

function buildChecklist(activeKey: ChecklistItem['key'] | null, doneThrough: ChecklistItem['key'][] = []) {
  return CHECKLIST_TEMPLATE.map((item) => {
    if (doneThrough.includes(item.key)) {
      return { ...item, status: 'done' as const }
    }

    if (item.key === activeKey) {
      return { ...item, status: 'running' as const }
    }

    return { ...item, status: 'pending' as const }
  })
}

function buildChecklistForStatus(status: ExtractionRecord['status'] | null) {
  if (status === 'completed') {
    return buildChecklist(null, ['received', 'queued', 'processing'])
  }

  if (status === 'failed') {
    return buildChecklist(null, ['received', 'queued'])
  }

  if (status === 'processing') {
    return buildChecklist('processing', ['received', 'queued'])
  }

  if (status === 'queued') {
    return buildChecklist('queued', ['received'])
  }

  return buildChecklist('received')
}

const POLL_INTERVAL_MS = 2000

export function ExtractionSessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<ExtractionSession | null>(null)
  const previewUrlRef = useRef<string | null>(null)
  const pollTimerRef = useRef<number | null>(null)
  const activeRequestRef = useRef(0)

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }, [])

  const resetSession = useCallback(() => {
    activeRequestRef.current += 1
    clearPollTimer()
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setSession(null)
  }, [clearPollTimer])

  useEffect(() => {
    return () => {
      clearPollTimer()
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
        previewUrlRef.current = null
      }
    }
  }, [clearPollTimer])

  const schedulePoll = useCallback(
    (requestId: number, extractionId: string) => {
      const poll = async () => {
        if (activeRequestRef.current !== requestId) return

        try {
          const latest = await fetchExtraction(extractionId)
          if (activeRequestRef.current !== requestId) return

          if (latest.status === 'completed') {
            clearPollTimer()
            setSession((current) =>
              current
                ? {
                    ...current,
                    status: 'completed',
                    response: latest,
                    error: null,
                    checklist: buildChecklistForStatus(latest.status),
                  }
                : current,
            )
            return
          }

          if (latest.status === 'failed') {
            clearPollTimer()
            setSession((current) =>
              current
                ? {
                    ...current,
                    status: 'failed',
                    response: latest,
                    error: latest.error_message || latest.message || 'OCR processing failed.',
                    checklist: buildChecklistForStatus(latest.status),
                  }
                : current,
            )
            return
          }

          setSession((current) =>
            current
              ? {
                  ...current,
                  status: 'processing',
                  response: latest,
                  error: null,
                  checklist: buildChecklistForStatus(latest.status),
                }
              : current,
          )

          if (activeRequestRef.current !== requestId) return
          pollTimerRef.current = window.setTimeout(poll, POLL_INTERVAL_MS)
        } catch (error) {
          if (activeRequestRef.current !== requestId) return

          clearPollTimer()
          setSession((current) =>
            current
              ? {
                  ...current,
                  status: 'error',
                  error: error instanceof Error ? error.message : 'Unable to refresh extraction status.',
                }
              : current,
          )
        }
      }

      clearPollTimer()
      pollTimerRef.current = window.setTimeout(poll, POLL_INTERVAL_MS)
    },
    [clearPollTimer],
  )

  const startExtraction = useCallback((file: File) => {
    activeRequestRef.current += 1
    const requestId = activeRequestRef.current
    clearPollTimer()

    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }

    const previewUrl = URL.createObjectURL(file)
    previewUrlRef.current = previewUrl

    setSession({
      file,
      previewUrl,
      status: 'uploading',
      response: null,
      error: null,
      checklist: buildChecklistForStatus('received'),
    })

    void (async () => {
      try {
        const response = await uploadExtractionImage(file)
        if (activeRequestRef.current !== requestId) return

        if (response.status === 'completed') {
          clearPollTimer()
          setSession((current) =>
            current
              ? {
                  ...current,
                  status: 'completed',
                  response,
                  error: null,
                  checklist: buildChecklistForStatus(response.status),
                }
              : current,
          )
          return
        }

        if (response.status === 'failed') {
          clearPollTimer()
          setSession((current) =>
            current
              ? {
                  ...current,
                  status: 'failed',
                  response,
                  error: response.error_message || response.message || 'OCR processing failed.',
                  checklist: buildChecklistForStatus(response.status),
                }
              : current,
          )
          return
        }

        setSession((current) =>
          current
            ? {
                ...current,
                status: 'processing',
                response,
                error: null,
                checklist: buildChecklistForStatus(response.status),
              }
            : current,
        )
        schedulePoll(requestId, response.id)
      } catch (error) {
        if (activeRequestRef.current !== requestId) return

        clearPollTimer()
        setSession((current) =>
          current
            ? {
                ...current,
                status: 'error',
                response: null,
                error: error instanceof Error ? error.message : 'Upload failed. Please try again.',
                checklist: buildChecklistForStatus(null),
              }
            : current,
        )
      }
    })()
  }, [clearPollTimer, schedulePoll])

  const value = useMemo(
    () => ({
      session,
      startExtraction,
      resetSession,
    }),
    [resetSession, session, startExtraction],
  )

  return <ExtractionSessionContext.Provider value={value}>{children}</ExtractionSessionContext.Provider>
}

export function useExtractionSession() {
  const context = useContext(ExtractionSessionContext)

  if (!context) {
    throw new Error('useExtractionSession must be used within ExtractionSessionProvider')
  }

  return context
}
