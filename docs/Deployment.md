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

## Local PostgreSQL

1. Copy `.env.example` to `.env` at the repository root.
2. Start the database and Redis services with `docker compose up -d postgres redis`.
3. Run Django migrations from `backend/`.
4. Start the backend, frontend, and a Celery worker against the same API URL.

### Worker

From `backend/`:

```bash
celery -A config worker -l info --concurrency=1
```
