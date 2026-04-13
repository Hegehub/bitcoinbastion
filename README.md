# Bitcoin Bastion

Production-minded Bitcoin-native intelligence and operations platform.

## Included production baseline
- Modular monolith with strict service/repository boundaries
- Versioned FastAPI API (`/api/v1/*`) with request ID middleware and standardized error handling
- Auth foundation (register/login + JWT)
- SQLAlchemy domain models for intelligence + auth + entities + audit logs
- Celery orchestration baseline with worker/beat services
- RSS ingestion, deduplication, scoring, signal engine, Telegram formatter
- Docker compose stack for app + db + redis + worker + beat

## Quick start
```bash
cp .env.example .env
make install-dev
make test
make up
```

## Why `make test` failed with `pytest: No such file or directory`
This happens when `pytest` is not installed in the active Python environment.
The Makefile now calls `python -m pytest` and includes `make install-dev` to install test dependencies first.

## Local run
```bash
make install-dev
make run
```

## API groups
- health
- auth
- news
- signals
- onchain
- entities
- wallet
- fees
- treasury
- admin
- users
- policy
- privacy
- education
- observability

## Operations endpoints
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /metrics`
