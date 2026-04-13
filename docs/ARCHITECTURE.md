# Architecture

## Style
Modular monolith with clear boundaries:
- `api` for transport
- `services` for business orchestration
- `db/repositories` for persistence access
- `integrations` for external providers
- `tasks` for asynchronous orchestration

## Runtime components
- FastAPI app process
- Celery worker process
- Celery beat scheduler
- PostgreSQL
- Redis
