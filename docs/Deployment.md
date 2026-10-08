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
- `SESSION_COOKIE_SECURE` (`true` in production)
- `SESSION_COOKIE_SAMESITE` (`None` when frontend and backend are on separate production sites)

## Local PostgreSQL

1. Copy `.env.example` to `.env` at the repository root.
2. Start the database and Redis services with `docker compose up -d postgres redis`.
3. Run Django migrations from `backend/`.
4. Start the backend, frontend, and a Celery worker against the same API URL.

Configure the Google OAuth web client ID in both `GOOGLE_CLIENT_ID` and `VITE_GOOGLE_CLIENT_ID`, and add the deployed frontend origin to the OAuth client’s authorized JavaScript origins.

### Worker

From `backend/`:

```bash
celery -A config worker -l info --concurrency=1
```
