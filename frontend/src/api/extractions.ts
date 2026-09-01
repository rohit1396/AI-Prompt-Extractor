export type ExtractionRecord = {
  id: string
  status: string
  filename: string
  content_type: string
  file_size?: number
  extracted_text: string
  message: string
  error_message?: string
  processing_time_ms?: number | null
  created_at?: string
  updated_at?: string
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parseExtractionResponse(response: Response): Promise<ExtractionRecord | null> {
  return (await response.json().catch(() => null)) as ExtractionRecord | null
}

function buildErrorMessage(
  payload: ExtractionRecord | { detail?: string; non_field_errors?: string[] } | null,
  fallback: string,
) {
  if (payload && 'detail' in payload && payload.detail) {
    return payload.detail
  }

  if (payload && 'non_field_errors' in payload && payload.non_field_errors?.[0]) {
    return payload.non_field_errors[0]
  }

  return fallback
}

export async function uploadExtractionImage(file: File): Promise<ExtractionRecord> {
  const formData = new FormData()
  formData.append('image', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/extractions/`, {
    method: 'POST',
    body: formData,
  })

  const payload = (await parseExtractionResponse(response)) as
    | ExtractionRecord
    | { detail?: string; non_field_errors?: string[] }
    | null

  if (!response.ok) {
    throw new Error(buildErrorMessage(payload, 'Upload failed. Please try again.'))
  }

  return payload as ExtractionRecord
}

export async function fetchExtraction(id: string): Promise<ExtractionRecord> {
  const response = await fetch(`${API_BASE_URL}/api/v1/extractions/${id}/`)
  const payload = (await parseExtractionResponse(response)) as
    | ExtractionRecord
    | { detail?: string; non_field_errors?: string[] }
    | null

  if (!response.ok) {
    throw new Error(buildErrorMessage(payload, 'Unable to refresh extraction status.'))
  }

  return payload as ExtractionRecord
}
