export type ExtractionResponse = {
  id: string
  status: string
  filename: string
  content_type: string
  extracted_text: string
  message: string
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function uploadExtractionImage(file: File): Promise<ExtractionResponse> {
  const formData = new FormData()
  formData.append('image', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/extractions/`, {
    method: 'POST',
    body: formData,
  })

  const payload = (await response.json().catch(() => null)) as
    | ExtractionResponse
    | { detail?: string; non_field_errors?: string[] }
    | null

  if (!response.ok) {
    const message =
      payload && 'detail' in payload && payload.detail
        ? payload.detail
        : payload && 'non_field_errors' in payload && payload.non_field_errors?.[0]
          ? payload.non_field_errors[0]
        : 'Upload failed. Please try again.'
    throw new Error(message)
  }

  return payload as ExtractionResponse
}
