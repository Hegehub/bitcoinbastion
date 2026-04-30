#!/usr/bin/env python
"""Validate model-table coverage in Alembic migrations.

Checks that every SQLAlchemy model table appears in at least one `op.create_table()`
call in migration revisions and that migrations do not create tables absent from
current model metadata.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.base import Base
import app.db.models  # noqa: F401  # ensure models are registered

CREATE_TABLE_RE = re.compile(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]")


def main() -> int:
    model_tables = set(Base.metadata.tables.keys())

    migration_tables: set[str] = set()
    for revision in Path("app/db/migrations/versions").glob("*.py"):
        migration_tables.update(CREATE_TABLE_RE.findall(revision.read_text()))

    missing_in_migrations = sorted(model_tables - migration_tables)
    missing_in_models = sorted(migration_tables - model_tables)

    print(
        "Model/Migration table coverage:",
        f"models={len(model_tables)}",
        f"migrations={len(migration_tables)}",
        f"missing_in_migrations={len(missing_in_migrations)}",
        f"missing_in_models={len(missing_in_models)}",
    )

    if missing_in_migrations:
        print("Tables in models but not migrations:", ", ".join(missing_in_migrations))
    if missing_in_models:
        print("Tables in migrations but not models:", ", ".join(missing_in_models))

    return 0 if not missing_in_migrations and not missing_in_models else 1


if __name__ == "__main__":
    raise SystemExit(main())
