#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
DB_FILE="${TMP_DIR}/repro.db"
DB_URL="sqlite+pysqlite:///${DB_FILE}"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

cd "${REPO_ROOT}"

DATABASE_URL="${DB_URL}" python -m alembic upgrade head >/dev/null
VERSION_1="$(DATABASE_URL="${DB_URL}" python - <<'PY'
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    print(conn.execute(text('select version_num from alembic_version')).scalar_one())
PY
)"

DATABASE_URL="${DB_URL}" python -m alembic downgrade base >/dev/null
DATABASE_URL="${DB_URL}" python -m alembic upgrade head >/dev/null
VERSION_2="$(DATABASE_URL="${DB_URL}" python - <<'PY'
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    print(conn.execute(text('select version_num from alembic_version')).scalar_one())
PY
)"

if [[ "${VERSION_1}" != "${VERSION_2}" ]]; then
  echo "Alembic reproducibility check failed: ${VERSION_1} != ${VERSION_2}" >&2
  exit 1
fi

echo "Alembic reproducibility check passed at revision ${VERSION_2}."
