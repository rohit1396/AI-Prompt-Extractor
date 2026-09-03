# Database

## Current State

The backend now persists extraction records in PostgreSQL-ready Django models.
SQLite is still available as a local fallback, but the project can be pointed at PostgreSQL through environment variables.

## Extraction Table

The `Extraction` model stores the first durable record for the app:

- `id`: UUID primary key
- `image`: uploaded file path
- `original_filename`: original client filename
- `file_size`: bytes
- `content_type`: image MIME type
- `status`: `received`, `queued`, `processing`, `completed`, `failed`
- `extracted_text`: OCR output
- `message`: user-facing status message
- `error_message`: backend error detail
- `processing_time_ms`: total processing duration
- `created_at`: creation timestamp
- `updated_at`: last update timestamp

## Local Setup

Use the root `.env.example` as the starting point.

For PostgreSQL-based development:

- start the database with `docker compose up -d postgres redis`
- set `DATABASE_URL=postgresql://promptlens:promptlens@localhost:5432/promptlens`
- set `CELERY_BROKER_URL=redis://localhost:6379/0`
- run `python manage.py migrate`

If PostgreSQL is not available yet, Django will fall back to SQLite so the project still boots during early development.
