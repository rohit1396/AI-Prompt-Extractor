# Roadmap: Frontend-Backend Integration

## Goal
Turn the current frontend prototype and Django scaffold into a working end-to-end prompt extraction product.

## Phase 1: MVP API
- Create a Django app for prompt extraction.
- Add an upload endpoint for screenshots.
- Add a result endpoint to fetch processed output.
- Define request and response contracts.

## Phase 2: OCR Pipeline
- Add image preprocessing.
- Integrate PaddleOCR.
- Clean and normalize extracted text.
- Return a structured prompt draft.

## Phase 3: Frontend Integration
- Replace the simulated processing flow with real API calls.
- Upload files to the backend.
- Show job progress and final extracted prompt.
- Add error, retry, and empty states.

## Phase 4: Persistence and History
- Store uploads and extraction results.
- Add a history view.
- Allow reopening past extractions.
- Add metadata such as timestamp, file type, and status.

## Phase 5: Hardening and Ship Readiness
- Add tests for frontend and backend.
- Fill out API, architecture, and deployment docs.
- Add upload validation and security checks.
- Prepare deployment config and environment handling.

## Suggested Priority
- P0: Phase 1 and Phase 2
- P1: Phase 3
- P2: Phase 4
- P3: Phase 5

## Recommended Execution Order
1. API contract and upload endpoint
2. OCR pipeline
3. Frontend integration
4. Persistence and history
5. Tests and deployment hardening

#2. OCR Pipeline : 

# OCR Prompt Extraction MVP

  ## Summary

  Build a backend OCR pipeline that accepts a user-uploaded screenshot, extracts visible prompt text from the image, and returns the cleaned text to the frontend immediately. This stays
  synchronous for now and reuses the existing upload flow, so the next phase can add prompt optimization on top of a stable extraction result.

  ## Key Changes

  - Backend OCR pipeline:
      - Replace the dummy upload response with real OCR processing in the upload endpoint.
      - Use PaddleOCR as the default engine, since it is already in the repo and better matches the current stack.
      - Add lightweight preprocessing before OCR, focused on screenshot readability rather than aggressive image transformation.
      - Normalize OCR output into a single extracted text block, with basic line merging and whitespace cleanup.

  - API contract:
      - Keep POST /api/v1/extractions/ as the main entry point.
      - Return the uploaded file metadata plus the extracted prompt text in the response.
      - Include a status field and a friendly message so the frontend can show “processing complete” without needing a second request.

  - Frontend integration:
      - Update the upload flow to render the extracted prompt text on the processing/results screen.
      - Keep the current upload and loading UI, but replace the dummy backend message with the actual OCR output.
      - Add an error state for OCR failures or unreadable images.

  - Validation and constraints:
      - Keep existing image type and size validation.
      - Treat OCR as best-effort extraction, not prompt optimization.
      - If no readable text is found, return a clear empty-result response rather than pretending extraction succeeded.

  - Backend:
      - Upload a valid screenshot containing prompt text and confirm the response includes extracted text.
      - Upload a screenshot with no readable prompt text and confirm the API returns an empty or explicit no-text response.
      - Upload an unsupported file type and confirm validation still rejects it.
      - Upload an oversized image and confirm validation still rejects it.

  - OCR quality checks:
      - Use a few representative screenshots from social media/chat UI layouts.
      - Confirm the pipeline handles multi-line text and common screenshot noise.

  - Frontend:
      - Confirm the UI shows the extracted text returned by the API.
      - Confirm loading, success, and error states still work with the real OCR response.

  ## Assumptions

  - The first version is synchronous and does not create a persisted extraction job or history entry.
  - PaddleOCR is the preferred engine for the initial implementation.
  - The goal for this task is extraction only, not prompt rewriting or optimization.
  - The existing upload endpoint remains the public API surface for now, so the frontend integration stays simple.