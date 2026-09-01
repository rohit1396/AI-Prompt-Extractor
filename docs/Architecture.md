# Architecture

# Make OCR Fast and Reliable Locally and in Production

  ## Summary

  Move OCR out of the HTTP request path. Right now the backend is synchronous: the upload request waits for PaddleOCR to finish, so on a low-resource production instance a slow OCR run can
  hit the web server timeout and surface as 502. The fix is a two-part change: an async job workflow for the app, and a deployment setup that gives OCR enough memory/CPU to finish
  reliably.

  ## Key Changes

  1. Split upload from processing.
      - POST /api/v1/extractions/ should only validate and store the file, create an extraction record, and return immediately with a job/extraction id.
      - Add GET /api/v1/extractions/<id>/ or GET /api/v1/extractions/<id>/status/ so the frontend can poll for progress and final text.
      - Keep the existing upload endpoint contract as stable as possible, but stop doing OCR inside that request.

  2. Add a background worker for OCR.
      - Use a Celery worker with Redis as the queue for the actual OCR step.
      - The worker should load the image, run preprocessing, call PaddleOCR, normalize the text, and update the extraction row in the database.
      - Store status transitions in the DB: received -> queued -> processing -> completed/failed.

  3. Make the frontend wait by polling, not by blocking.
      - After upload, navigate to a “processing” screen immediately.
      - Poll the extraction status endpoint every few seconds until it reaches completed or failed.
      - Show a timeout-friendly UI: “still working”, “retry”, and “failed due to server overload” states.

  4. Tune OCR for constrained environments.
      - Reduce image size before OCR.
      - Keep preprocessing lightweight and deterministic.
      - Limit OCR concurrency to 1 worker on small machines.
      - Add hard caps on file size and image dimensions so production does not accept inputs that are too expensive for the host.

  5. Fix production deployment assumptions.
      - Do not rely on the web dyno/request worker to also do OCR work.
      - If Railway free plan cannot support a separate worker with enough RAM, OCR should run on a better-capacity worker or a different service tier.
      - Keep the web app and OCR worker separately observable so timeouts are easy to diagnose.

  ## Implementation Steps

  1. Change the backend API flow.
      - Update the upload endpoint to create an extraction record and enqueue OCR work.
      - Add a status/result endpoint.
      - Keep response payloads explicit so the frontend can render progress immediately.

  2. Introduce a background execution path.
      - Add a worker process for OCR execution.
      - Persist errors and processing duration in the extraction record.
      - Make the worker idempotent so retries do not duplicate work.

  3. Update the frontend flow.
      - Replace the current “wait for upload response to contain final OCR text” behavior.
      - Show upload success as “processing started”.
      - Poll until the result is ready.
      - Preserve the current image preview and extracted-text result display.

  4. Add resiliency.
      - Add request and worker timeouts that fail cleanly instead of hanging.
      - Add retry logic for transient OCR failures.
      - Return a readable error when the worker cannot complete due to memory or model-loading issues.

  5. Tune deployment.
      - Run the web server with a conservative timeout and only HTTP handling responsibilities.
      - Run OCR on a separate worker with enough memory for PaddleOCR.
      - If production resources remain too small, switch the OCR worker to a more capable host or plan.

  6. Verify with local and production-like tests.
      - Test small and large images locally.
      - Test concurrent uploads.
      - Test worker restart and retry behavior.
      - Test against a low-memory environment profile to confirm the app degrades gracefully instead of producing 502.

  - Backend:
      - Upload returns quickly and creates a pending extraction.
      - Status endpoint transitions from queued/processing to completed.
      - OCR failure marks the record failed and returns a clean error.
      - Oversized and unsupported uploads still reject correctly.

  - Frontend:
      - Upload starts processing immediately.
      - Polling stops on completion or failure.
      - Error and retry states render correctly.
      - Final extracted text displays from the result endpoint.

  - Deployment:
      - Web request completes well under the host timeout.
      - Worker can process one image end-to-end without OOM on the target environment.
      - Production logs clearly show whether a failure happened in upload, queueing, or OCR execution.

  ## Assumptions

  - The current problem is primarily architectural, not just a bug in the OCR model.
  - Moving OCR off the request path is necessary even if the model itself stays unchanged.
  - A 1 vCPU / 512 MB production instance is likely too small for reliable inline PaddleOCR processing.
  - If production cannot provide a separate worker with enough resources, the app will need either a more capable plan or a lighter OCR backend for production.
