# Architecture

## System style
Bitcoin Bastion is implemented as a **modular monolith** with explicit boundaries that keep business logic out of transport layers.

Primary boundaries:
- `app/api`: FastAPI route handlers, dependencies, middleware, error envelopes.
- `app/services`: orchestration and domain logic (scoring, policy, explainability, wallet/treasury, delivery).
- `app/db/models`: relational domain models.
- `app/db/repositories`: persistence access patterns and pagination/query helpers.
- `app/integrations`: external provider adapters (RSS, Bitcoin provider abstractions).
- `app/tasks`: Celery entrypoints for scheduled and async workflows.
- `app/schemas`: request/response and envelope contracts.

## Runtime topology
Core runtime components:
1. **API process** (FastAPI / Uvicorn)
2. **Celery worker** (task execution)
3. **Celery beat** (scheduled jobs)
4. **PostgreSQL** (durable state)
5. **Redis** (Celery broker/result + cache-ready layer)

## Request lifecycle
1. Request enters API with request ID middleware and rate limiting middleware.
2. Route validates input schema and delegates to service layer.
3. Service orchestrates repositories/integrations.
4. Results are wrapped in standardized response envelopes.
5. Metrics and error handlers provide observability and stable failure contracts.

## Current intelligence pipeline shape
- **Ingestion**: RSS ingestion service + on-chain ingestion service.
- **Scoring**: News scoring and fee/wallet/privacy scoring services.
- **Signals**: Signal engine + explainability service with evidence graph persistence.
- **Delivery**: Telegram formatter/delivery service + delivery logs.
- **Governance**: Policy runtime checks and execution logs.

## Design constraints
- Thin routes and thin Telegram handlers.
- Explainability-first for scores and recommendations.
- Retry-safe and idempotency-aware background tasks.
- Security baseline through JWT auth, RBAC-oriented dependencies, and audit logs.

## Schema governance notes
- Alembic is the source of schema evolution truth; `create_all()` is not a deployment path.
- Current schema truth audit confirms complete table coverage for all SQLAlchemy model tables (27/27 mapped through migrations).
- SQLite-specific migration behavior (batch mode, default/constraint representation) can produce autogenerate drift signals that require explicit review before accepting migration deltas.
