#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"
: "${REDIS_URL:?REDIS_URL must be set}"
: "${JWT_SECRET_KEY:?JWT_SECRET_KEY must be set}"
: "${ENVIRONMENT:=dev}"

if [[ "${ENVIRONMENT}" == "prod" || "${ENVIRONMENT}" == "production" ]]; then
  if [[ "${JWT_SECRET_KEY}" == "change-me-in-prod" || ${#JWT_SECRET_KEY} -lt 32 ]]; then
    echo "Refusing startup: JWT_SECRET_KEY is insecure for production." >&2
    exit 1
  fi
fi

python -m alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
