# Deployment

## Required Environment Variables

Place these values in the root `.env` file. The backend loads it automatically and the frontend reads the same file through Vite.

- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or the `POSTGRES_*` variables
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `USE_CLOUDINARY_STORAGE`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `CLOUDINARY_UPLOAD_FOLDER`
- `VITE_API_BASE_URL`
- `GOOGLE_CLIENT_ID`
- `VITE_GOOGLE_CLIENT_ID`
- `SENTRY_DSN` (optional backend and Celery monitoring)
- `SENTRY_ENVIRONMENT`
- `SENTRY_RELEASE`
- `SENTRY_TRACES_SAMPLE_RATE` (use `0` until performance tracing is enabled)
- `VITE_SENTRY_DSN` (optional browser monitoring)
- `VITE_SENTRY_ENVIRONMENT`
- `VITE_SENTRY_RELEASE`
- `SESSION_COOKIE_SECURE` (`true` in production)
- `SESSION_COOKIE_SAMESITE` (`None` when frontend and backend are on separate production sites)

## Local PostgreSQL

1. Copy `.env.example` to `.env` at the repository root.
2. Start the database and Redis services with `docker compose up -d postgres redis`.
3. Run Django migrations from `backend/`.
4. Start the backend, frontend, and a Celery worker against the same API URL.

Configure the Google OAuth web client ID in both `GOOGLE_CLIENT_ID` and `VITE_GOOGLE_CLIENT_ID`, and add the deployed frontend origin to the OAuth client’s authorized JavaScript origins.

Configure separate Sentry projects for the browser and backend. The Celery worker uses the backend DSN and is tagged by its task context. Set `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, and `SENTRY_PROJECT` only in the frontend build environment so Vite can upload source maps; do not put these values in the repository `.env` used by the browser.

Sentry events include user ID/email and extraction metadata such as status, file type, size, timing, and extraction ID. Images, request bodies, OCR text, prompts, credentials, and cookies are filtered before events are sent.

### Worker

From `backend/`:

```bash
celery -A config worker -l info --concurrency=1
```
