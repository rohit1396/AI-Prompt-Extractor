
  # Phase 1 Plan: MVP Backend API for Prompt Extraction

  ## Summary

  Build the first backend slice needed for the product: a Django REST API that accepts screenshot uploads, persists a job record, and exposes a retrieval endpoint for status/result lookup.
  Use PostgreSQL as the intended database service from the start, with Django configured through environment variables so the backend can run locally or in deployment without code changes.

  ## Step-by-Step Implementation

  1. Create the backend app boundary
      - Add a dedicated Django app for extraction.
      - Register rest_framework and corsheaders.
      - Keep the app focused on upload, job tracking, and retrieval.

  2. Set up database configuration
      - Configure Django to read database settings from environment variables.
      - Use PostgreSQL as the default target database service.
      - Keep a local fallback only if needed for quick developer bootstrapping, but do not design phase 1 around SQLite.
      - Run initial migrations against the chosen database.

  3. Define the core data model
      - Create one primary model to represent an extraction job.
      - Store:
          - UUID primary key
          - uploaded file
          - original filename
          - file size
          - content type
          - status
          - created/updated timestamps
          - nullable result fields for later phases
          - nullable error message

      - Use status values like received, processing, completed, failed.

  4. Set up file upload handling
      - Configure MEDIA_ROOT and MEDIA_URL.
      - Add file validation for:
          - allowed image types
          - maximum upload size

      - Store uploads locally for phase 1 unless a separate object storage decision is made later.

  5. Create API serializers and validation
      - Add an upload serializer for multipart form data.
      - Validate required file input, file type, and size.
      - Add a response serializer with a stable schema for the frontend.

  6. Implement the upload endpoint
      - Add POST /api/v1/extractions/.
      - Behavior:
          - validate the uploaded image
          - create a job record
          - save the file
          - return the created job with its UUID and status

      - Keep the endpoint synchronous for now, but make the record shape compatible with async processing later.

  7. Implement the retrieval endpoint
      - Add GET /api/v1/extractions/<uuid>/.
      - Behavior:
          - fetch the job by UUID
          - return status, metadata, and any available result fields
          - return 404 for unknown IDs

  8. Wire API URLs and admin
      - Add versioned API routing under /api/v1/.
      - Register the extraction model in Django admin.
      - Add useful admin list display and filters for debugging.

  9. Document the API contract
      - Fill in docs/API.md with:
          - endpoint paths
          - request format
          - response schema
          - status codes
          - validation errors

      - Include an example request for manual verification.

  10. Add tests

  - Cover:
      - successful upload
      - missing file validation
      - unsupported file type
      - file too large
      - successful retrieval
      - 404 on unknown UUID

  - Verify response schema and status codes, not just persistence.

  ## Public API / Interface

  - POST /api/v1/extractions/
      - multipart form-data
      - input: image file
      - output: created extraction job record
      - output: job metadata, status, and result fields if present

  ## Test Plan

  - Upload a valid PNG/JPG screenshot and confirm the API returns a created job record.
  - Submit a request without a file and confirm validation errors.
  - Submit a non-image file and confirm rejection.
  - Request an unknown UUID and confirm 404.
  - Confirm the returned payload shape is stable enough for the frontend to consume in phase 3.

  ## Assumptions

  - Phase 1 is backend-only and does not implement OCR.
  - PostgreSQL is the real database target for the project.
  - Local SQLite, if kept at all, is only a temporary developer convenience.
  - Uploaded files are stored locally for phase 1 unless we decide to introduce object storage later.
  - The frontend remains simulated until the backend contract is in place.
