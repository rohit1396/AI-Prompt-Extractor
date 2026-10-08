import * as Sentry from '@sentry/react'

const sentryDsn = import.meta.env.VITE_SENTRY_DSN

export function initializeSentry() {
  if (!sentryDsn) return

  Sentry.init({
    dsn: sentryDsn,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT ?? 'development',
    release: import.meta.env.VITE_SENTRY_RELEASE || undefined,
    tracesSampleRate: 0,
    beforeSend(event) {
      if (event.request) {
        delete event.request.data
        delete event.request.cookies
        if (event.request.headers) {
          delete event.request.headers.authorization
          delete event.request.headers.cookie
          delete event.request.headers['x-csrftoken']
        }
      }
      if (event.extra) {
        delete event.extra.file
        delete event.extra.ocr_text
        delete event.extra.raw_ocr_text
        delete event.extra.extracted_text
        delete event.extra.prompt
        delete event.extra.optimized_prompt
      }
      return event
    },
  })
}

export function captureFrontendException(
  error: unknown,
  operation: string,
  context: Record<string, string | number | boolean | undefined> = {},
) {
  if (!sentryDsn) return

  Sentry.withScope((scope) => {
    scope.setTag('operation', operation)
    Object.entries(context).forEach(([key, value]) => {
      if (value !== undefined) scope.setTag(key, String(value))
    })
    Sentry.captureException(error)
  })
}

export { Sentry }
