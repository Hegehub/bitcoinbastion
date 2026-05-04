#!/usr/bin/env python
"""Validate runtime schema parity between SQLAlchemy metadata and migrated DB schema.

This check is intentionally conservative:
- validates table set parity
- validates per-table column set parity
- validates nullable parity

It does not currently enforce strict SQL type identity across dialect nuances.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.config import get_settings
from app.db.base import Base
import app.db.models  # noqa: F401


def main() -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url, future=True)
    inspector = inspect(engine)

    model_tables = set(Base.metadata.tables.keys())
    db_tables = {name for name in inspector.get_table_names() if name != "alembic_version"}

    missing_tables = sorted(model_tables - db_tables)
    extra_tables = sorted(db_tables - model_tables)

    errors: list[str] = []
    if missing_tables:
        errors.append(f"missing tables in DB: {', '.join(missing_tables)}")
    if extra_tables:
        errors.append(f"extra tables in DB: {', '.join(extra_tables)}")

    nullable_mismatches: list[str] = []
    column_mismatches: list[str] = []
    for table_name in sorted(model_tables & db_tables):
        model_columns = Base.metadata.tables[table_name].columns
        model_column_names = {col.name for col in model_columns}
        db_columns_raw = inspector.get_columns(table_name)
        db_column_names = {col["name"] for col in db_columns_raw}

        missing_cols = sorted(model_column_names - db_column_names)
        extra_cols = sorted(db_column_names - model_column_names)
        if missing_cols or extra_cols:
            column_mismatches.append(
                f"{table_name}: missing={missing_cols or []}, extra={extra_cols or []}"
            )

        db_nullable = {col["name"]: bool(col.get("nullable", True)) for col in db_columns_raw}
        for model_col in model_columns:
            if model_col.name not in db_nullable:
                continue
            if bool(model_col.nullable) != db_nullable[model_col.name]:
                nullable_mismatches.append(
                    f"{table_name}.{model_col.name}: model_nullable={bool(model_col.nullable)} db_nullable={db_nullable[model_col.name]}"
                )

    if column_mismatches:
        errors.append("column parity mismatch: " + "; ".join(column_mismatches))
    if nullable_mismatches:
        errors.append("nullable parity mismatch: " + "; ".join(nullable_mismatches))

    print(
        "Runtime schema parity:",
        f"model_tables={len(model_tables)}",
        f"db_tables={len(db_tables)}",
        f"errors={len(errors)}",
    )
    if errors:
        for err in errors:
            print("-", err)
        return 1
    print("Schema runtime parity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
