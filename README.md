# ZeroBite v2

Real-time food donation and waste-management platform. Connects restaurants,
event organizers, and individual donors who have surplus food with NGOs and
volunteers who can collect it before it expires.

## Stack

- **Backend**: Django 5, Django REST Framework, SimpleJWT, Celery + Redis,
  Django Channels, PostgreSQL.
- **Frontend**: React 18 + Vite + TypeScript, TanStack Query, Axios,
  React Router.
- **Infra**: Docker Compose (api, web, db, redis, worker, beat).

## Prerequisites

- Docker and Docker Compose
- (Optional, for running outside Docker) Python 3.12+, Node 20+, PostgreSQL 16,
  Redis 7

## Getting started

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set `SECRET_KEY` to something unique. The defaults for
   `DATABASE_URL` and `REDIS_URL` target the Compose services (`db` and
   `redis`), so they work as-is for local development.

2. Build and start everything:

   ```bash
   docker compose up --build
   ```

3. Open:

   - Frontend: http://localhost:5173
   - Backend health: http://localhost:8000/api/health/
   - API docs (Swagger): http://localhost:8000/api/docs/

   The Home page should display **Backend: ok** once the API is up.

## Running tests

Backend tests run inside the `api` container against the Compose database:

```bash
docker compose run --rm api pytest
```

Frontend tests (none yet, Vitest is wired):

```bash
docker compose run --rm web npm test
```

## Common commands

```bash
# Start in the background
docker compose up -d --build

# Tail logs
docker compose logs -f api

# Open a Django shell
docker compose run --rm api python manage.py shell

# Create a superuser
docker compose run --rm api python manage.py createsuperuser

# Stop and remove containers (keeps the db volume)
docker compose down

# Stop and remove containers AND the db volume
docker compose down -v
```

## Project layout

```
.
├── backend/           Django project (config, apps, tests)
├── frontend/          Vite + React + TS app
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

## Environment variables

All configuration comes from environment variables. See `.env.example` for the
full list. Key ones:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key (required) |
| `DEBUG` | `True` in dev, `False` in prod |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` or `config.settings.prod` |
| `DATABASE_URL` | Postgres DSN |
| `REDIS_URL` | Redis DSN (Celery broker + Channels layer) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `VITE_API_URL` | Frontend base URL for API calls |
| `VITE_MAP_PROVIDER` | `leaflet` (default) or `google` |
