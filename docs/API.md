# API

## POST `/api/v1/extractions/`

Uploads a single image and returns extracted prompt text.

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
  "status": "completed",
  "filename": "prompt.png",
  "content_type": "image/png",
  "extracted_text": "Create a cinematic portrait of a cyberpunk runner...",
  "message": "Prompt text extracted successfully."
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

`500 Internal Server Error`

```json
{
  "id": "2d2f3d0f-8e4c-4a71-bd4f-8dcf4ec8ed42",
  "status": "failed",
  "filename": "prompt.png",
  "content_type": "image/png",
  "extracted_text": "",
  "message": "Unable to extract text from the uploaded image."
}
```
