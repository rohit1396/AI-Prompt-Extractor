# Todo

## Phase 1
- Done: created a Django `api` app
- Done: added `POST /api/v1/extractions/`
- Done: backend accepts image uploads and returns a dummy JSON response
- Pending: add `GET /api/v1/extractions/<id>/`
- Partial: request/response contract exists only for upload

## Phase 2
- Not started: image preprocessing
- Not started: PaddleOCR integration
- Not started: text cleanup and prompt drafting

## Phase 3
- Done: frontend sends image to backend with `POST`
- Done: frontend uses a dedicated API module
- Done: frontend shows backend response on the processing page
- Partial: loading and error states exist, but flow still uses a dummy backend response

## Phase 4
- Not started: persistence
- Not started: history view
- Not started: reopen past extractions
- Not started: stored metadata and status tracking

## Phase 5
- Not started: backend tests
- Not started: frontend tests
- Not started: API docs
- Partial: upload validation and CORS are already in place

## Repo Hygiene
- Done: added `.gitignore` for `__pycache__/` and `*.pyc`
- Done: removed tracked `.pyc` files from the working tree
