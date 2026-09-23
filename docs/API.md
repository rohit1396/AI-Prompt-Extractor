# API

## POST `/api/v1/extractions/`

Uploads a single image, persists an extraction record, and queues OCR work.
The worker also classifies the OCR output so the API can distinguish prompt-like
text from ordinary text.

### Request

- Content type: `multipart/form-data`
- Field:
  - `image`: image file

### Validation

- Allowed types: `image/png`, `image/jpeg`, `image/webp`
- Max size: `10MB`

### Success response

`201 Created`

```json
{
  "id": "2d2f3d0f-8e4c-4a71-bd4f-8dcf4ec8ed42",
  "status": "queued",
  "filename": "prompt.png",
  "content_type": "image/png",
  "file_size": 482901,
  "image_url": "https://res.cloudinary.com/...",
  "storage_provider": "cloudinary",
  "cloudinary_public_id": "promptlens/extractions/...",
  "extracted_text": "",
  "is_prompt": false,
  "prompt_confidence": null,
  "raw_ocr_text": "",
  "classification_label": "",
  "classification_score": null,
  "classification_confidence": null,
  "matched_signals": [],
  "classifier_version": "",
  "message": "Image received. OCR job queued.",
  "error_message": "",
  "processing_time_ms": null,
  "created_at": "2026-08-11T10:18:42Z",
  "updated_at": "2026-08-11T10:18:43Z"
}
```

### Error responses

`400 Bad Request`

```json
{
  "image": [
    "Unsupported image type."
  ]
}
```

`503 Service Unavailable`

```json
{
  "id": "2d2f3d0f-8e4c-4a71-bd4f-8dcf4ec8ed42",
  "status": "failed",
  "filename": "prompt.png",
  "content_type": "image/png",
  "file_size": 482901,
  "image_url": "https://res.cloudinary.com/...",
  "storage_provider": "cloudinary",
  "cloudinary_public_id": "promptlens/extractions/...",
  "extracted_text": "",
  "is_prompt": false,
  "prompt_confidence": null,
  "raw_ocr_text": "",
  "classification_label": "",
  "classification_score": null,
  "classification_confidence": null,
  "matched_signals": [],
  "classifier_version": "",
  "message": "Unable to queue the OCR job.",
  "error_message": "Broker is unavailable.",
  "processing_time_ms": null,
  "created_at": "2026-08-11T10:18:42Z",
  "updated_at": "2026-08-11T10:18:43Z"
}
```

## GET `/api/v1/extractions/<id>/`

Returns the current persisted extraction state so the frontend can poll for progress.

The response shape matches the POST response, but `status` may be `received`, `queued`, `processing`, `completed`, or `failed`.

When OCR finishes successfully:

- `raw_ocr_text` and `extracted_text` contain the OCR output for every completed extraction, including `uncertain` and `not_prompt` classifications
- `is_prompt` is `true` when the classifier believes the text is prompt-like
- `prompt_confidence` is the prompt-evidence coverage (0–99), not a machine-learning probability
- `classification_label` is `prompt`, `not_prompt`, or `uncertain`
- `matched_signals` lists the weighted signals that contributed to the score

## GET `/api/v1/extractions/history/`

Returns a newest-first, paginated summary of all extraction attempts. The endpoint includes queued, processing, completed, and failed records.

### Query parameters

- `page`: 1-based page number (default `1`)
- `page_size`: number of records per page (default `20`, maximum `50`)

### Success response

`200 OK`

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/extractions/history/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": "2d2f3d0f-8e4c-4a71-bd4f-8dcf4ec8ed42",
      "status": "completed",
      "filename": "prompt.png",
      "content_type": "image/png",
      "file_size": 482901,
      "image_url": "https://res.cloudinary.com/...",
      "storage_provider": "cloudinary",
      "classification_label": "prompt",
      "classification_score": 12,
      "classification_confidence": 63,
      "message": "Prompt-like text extracted successfully.",
      "error_message": "",
      "processing_time_ms": 820,
      "created_at": "2026-08-11T10:18:42Z",
      "updated_at": "2026-08-11T10:18:43Z"
    }
  ]
}
```

The list intentionally omits OCR text and matched signals. Use the extraction detail endpoint with an item `id` when those full fields are needed.
