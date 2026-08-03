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
