# Deployment

## Required Environment Variables

- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or the `POSTGRES_*` variables
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `VITE_API_BASE_URL`

## Local PostgreSQL

1. Copy `.env.example` to your local environment file.
2. Start the database and Redis services with `docker compose up -d postgres redis`.
3. Run Django migrations from `backend/`.
4. Start the backend, frontend, and a Celery worker against the same API URL.

### Worker

From `backend/`:

```bash
celery -A config worker -l info --concurrency=1
```
