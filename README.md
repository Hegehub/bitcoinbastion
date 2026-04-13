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
make up
make test
```

## Local run
```bash
pip install -e '.[dev]'
uvicorn app.main:app --reload
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
