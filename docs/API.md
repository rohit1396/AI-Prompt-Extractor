# API

## POST `/api/v1/extractions/`

Uploads a single image, persists an extraction record, and queues OCR work.

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
