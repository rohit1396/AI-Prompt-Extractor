# PromptLens

AI-powered prompt extraction platform.

## Status

🚧 Under Development

## Tech Stack

Frontend
- React
- Vite
- TypeScript
- Tailwind CSS

Backend
- Django
- Django REST Framework
- PaddleOCR

## Project Structure

frontend/
backend/
docs/
dataset/

## Current Sprint

Sprint 1 - PostgreSQL persistence foundation

## Deployment Environment Variables

Local development:
- `VITE_API_BASE_URL=http://localhost:8000`
- `ALLOWED_HOSTS=localhost,127.0.0.1`
- `CORS_ALLOWED_ORIGINS=http://localhost:5173`
- `CSRF_TRUSTED_ORIGINS=http://localhost:5173`

Production:
- `VITE_API_BASE_URL=https://ai-prompt-extractor.onrender.com`
- `ALLOWED_HOSTS=ai-prompt-extractor.onrender.com`
- `CORS_ALLOWED_ORIGINS=https://ai-prompt-extractor-beta.vercel.app`
- `CSRF_TRUSTED_ORIGINS=https://ai-prompt-extractor-beta.vercel.app`

Backend database:
- `DATABASE_URL=postgresql://promptlens:promptlens@localhost:5432/promptlens`
- or `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
