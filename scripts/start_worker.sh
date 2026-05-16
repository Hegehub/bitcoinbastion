#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"
: "${REDIS_URL:?REDIS_URL must be set}"

python -m alembic upgrade head
exec celery -A app.tasks.celery_app.celery_app worker --loglevel=info
