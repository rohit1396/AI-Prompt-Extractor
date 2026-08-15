# Deployment

## Required Environment Variables

- `DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or the `POSTGRES_*` variables
- `VITE_API_BASE_URL`

## Local PostgreSQL

1. Copy `.env.example` to your local environment file.
2. Start the database service with `docker compose up -d postgres`.
3. Run Django migrations from `backend/`.
4. Start the backend and frontend against the same API URL.
