/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import type { ExtractionResponse } from '../api/extractions'
import { uploadExtractionImage } from '../api/extractions'

export type ChecklistItem = {
  key: 'received' | 'preprocess' | 'ocr'
  label: string
  status: 'pending' | 'running' | 'done'
}

export type ExtractionSession = {
  file: File
  previewUrl: string
  status: 'idle' | 'uploading' | 'completed' | 'error'
  response: ExtractionResponse | null
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
  { key: 'preprocess', label: 'Preprocessing done' },
  { key: 'ocr', label: 'OCR extraction in progress' },
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

export function ExtractionSessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<ExtractionSession | null>(null)
  const previewUrlRef = useRef<string | null>(null)
  const timersRef = useRef<number[]>([])
  const activeRequestRef = useRef(0)

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((timer) => window.clearTimeout(timer))
    timersRef.current = []
  }, [])

  const resetSession = useCallback(() => {
    activeRequestRef.current += 1
    clearTimers()
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setSession(null)
  }, [clearTimers])

  useEffect(() => {
    return () => {
      clearTimers()
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
        previewUrlRef.current = null
      }
    }
  }, [clearTimers])

  const startExtraction = useCallback((file: File) => {
    activeRequestRef.current += 1
    const requestId = activeRequestRef.current
    clearTimers()

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
      checklist: buildChecklist('received'),
    })

    timersRef.current.push(
      window.setTimeout(() => {
        if (activeRequestRef.current !== requestId) return
        setSession((current) =>
          current
            ? {
                ...current,
                checklist: buildChecklist('preprocess', ['received']),
              }
            : current,
        )
      }, 500),
    )

    timersRef.current.push(
      window.setTimeout(() => {
        if (activeRequestRef.current !== requestId) return
        setSession((current) =>
          current
            ? {
                ...current,
                checklist: buildChecklist('ocr', ['received', 'preprocess']),
              }
            : current,
        )
      }, 1200),
    )

    void (async () => {
      try {
        const response = await uploadExtractionImage(file)
        if (activeRequestRef.current !== requestId) return

        clearTimers()
        setSession((current) =>
          current
            ? {
                ...current,
                status: 'completed',
                response,
                error: null,
                checklist: buildChecklist(null, ['received', 'preprocess', 'ocr']),
              }
            : current,
        )
      } catch (error) {
        if (activeRequestRef.current !== requestId) return

        clearTimers()
        setSession((current) =>
          current
            ? {
                ...current,
                status: 'error',
                response: null,
                error: error instanceof Error ? error.message : 'Upload failed. Please try again.',
                checklist: buildChecklist(null, []),
              }
            : current,
        )
      }
    })()
  }, [clearTimers])

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
