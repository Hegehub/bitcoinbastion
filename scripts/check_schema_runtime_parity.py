#!/usr/bin/env python
"""Validate runtime schema parity between SQLAlchemy metadata and migrated DB schema.

Checks:
- table set parity
- per-table column set parity
- nullable parity
- practical SQL type affinity parity
- index parity (name + column tuple + uniqueness)
- unique constraint parity
- foreign key parity (local/ref columns + target table)
- server default parity (best-effort, normalized textual compare)

Runs against a temporary SQLite database migrated to Alembic head.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql.schema import Column, ForeignKeyConstraint, Index, Table, UniqueConstraint
from sqlalchemy.sql.type_api import TypeEngine

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.base import Base  # noqa: E402
import app.db.models  # noqa: E402,F401


def _upgrade_schema(database_url: str) -> None:
    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def _types_have_same_affinity(model_type: TypeEngine, db_type: object) -> bool:
    if not isinstance(db_type, TypeEngine):
        return False
    return bool(model_type._compare_type_affinity(db_type))


def _normalize_default(value: object) -> str:
    raw = str(value or "")
    raw = raw.strip().lower()
    raw = raw.replace("::character varying", "")
    raw = raw.replace("::text", "")
    raw = re.sub(r"\s+", "", raw)
    if raw.startswith("(") and raw.endswith(")"):
        raw = raw[1:-1]
    return raw


def _model_index_signature(table: Table) -> set[tuple[str | None, tuple[str, ...], bool]]:
    signatures: set[tuple[str | None, tuple[str, ...], bool]] = set()
    for idx in table.indexes:
        if not isinstance(idx, Index):
            continue
        signatures.add((idx.name, tuple(col.name for col in idx.columns), bool(idx.unique)))
    return signatures


def _db_index_signature(
    inspector: Inspector, table_name: str
) -> set[tuple[str | None, tuple[str, ...], bool]]:
    signatures: set[tuple[str | None, tuple[str, ...], bool]] = set()
    try:
        for idx in inspector.get_indexes(table_name):
            signatures.add(
                (
                    idx.get("name"),
                    tuple(idx.get("column_names") or ()),
                    bool(idx.get("unique", False)),
                )
            )
    except NotImplementedError:
        return set()
    return signatures


def _model_unique_signature(table: Table) -> set[tuple[str | None, tuple[str, ...]]]:
    signatures: set[tuple[str | None, tuple[str, ...]]] = set()
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            signatures.add((constraint.name, tuple(col.name for col in constraint.columns)))
    for column in table.columns:
        if bool(column.unique):
            signatures.add((None, (column.name,)))
    return signatures


def _db_unique_signature(
    inspector: Inspector, table_name: str
) -> set[tuple[str | None, tuple[str, ...]]]:
    signatures: set[tuple[str | None, tuple[str, ...]]] = set()
    try:
        for constraint in inspector.get_unique_constraints(table_name):
            signatures.add((constraint.get("name"), tuple(constraint.get("column_names") or ())))
    except NotImplementedError:
        return set()
    return signatures


def _model_fk_signature(table: Table) -> set[tuple[tuple[str, ...], str, tuple[str, ...]]]:
    signatures: set[tuple[tuple[str, ...], str, tuple[str, ...]]] = set()
    for constraint in table.constraints:
        if isinstance(constraint, ForeignKeyConstraint):
            local_cols = tuple(col.name for col in constraint.columns)
            target_cols = tuple(element.column.name for element in constraint.elements)
            target_table = constraint.elements[0].column.table.name
            signatures.add((local_cols, target_table, target_cols))
    return signatures


def _db_fk_signature(
    inspector: Inspector, table_name: str
) -> set[tuple[tuple[str, ...], str, tuple[str, ...]]]:
    signatures: set[tuple[tuple[str, ...], str, tuple[str, ...]]] = set()
    try:
        for fk in inspector.get_foreign_keys(table_name):
            signatures.add(
                (
                    tuple(fk.get("constrained_columns") or ()),
                    str(fk.get("referred_table") or ""),
                    tuple(fk.get("referred_columns") or ()),
                )
            )
    except NotImplementedError:
        return set()
    return signatures


def _model_server_default(column: Column) -> str:
    if column.server_default is None:
        return ""
    default_arg = getattr(column.server_default, "arg", column.server_default)
    return _normalize_default(default_arg)


def collect_schema_parity_errors(inspector: Inspector) -> list[str]:
    model_tables = set(Base.metadata.tables.keys())
    db_tables = {name for name in inspector.get_table_names() if name != "alembic_version"}

    errors: list[str] = []
    missing_tables = sorted(model_tables - db_tables)
    extra_tables = sorted(db_tables - model_tables)
    if missing_tables:
        errors.append(f"missing tables in DB: {', '.join(missing_tables)}")
    if extra_tables:
        errors.append(f"extra tables in DB: {', '.join(extra_tables)}")

    column_mismatches: list[str] = []
    nullable_mismatches: list[str] = []
    type_mismatches: list[str] = []
    index_mismatches: list[str] = []
    unique_mismatches: list[str] = []
    fk_mismatches: list[str] = []
    default_mismatches: list[str] = []

    for table_name in sorted(model_tables & db_tables):
        table = Base.metadata.tables[table_name]
        model_columns = table.columns
        model_column_names = {col.name for col in model_columns}
        db_columns_raw = inspector.get_columns(table_name)
        db_column_names = {col["name"] for col in db_columns_raw}

        missing_cols = sorted(model_column_names - db_column_names)
        extra_cols = sorted(db_column_names - model_column_names)
        if missing_cols or extra_cols:
            column_mismatches.append(
                f"{table_name}: missing={missing_cols or []}, extra={extra_cols or []}"
            )

        db_columns_by_name = {col["name"]: col for col in db_columns_raw}
        for model_col in model_columns:
            db_col = db_columns_by_name.get(model_col.name)
            if not db_col:
                continue

            db_nullable = bool(db_col.get("nullable", True))
            if bool(model_col.nullable) != db_nullable:
                nullable_mismatches.append(
                    f"{table_name}.{model_col.name}: model_nullable={bool(model_col.nullable)} db_nullable={db_nullable}"
                )

            db_type = db_col.get("type")
            if not _types_have_same_affinity(model_col.type, db_type):
                type_mismatches.append(
                    f"{table_name}.{model_col.name}: model_type={model_col.type} db_type={db_type}"
                )

            if model_col.server_default is not None:
                model_default = _model_server_default(model_col)
                db_default = _normalize_default(db_col.get("default"))
                if model_default != db_default:
                    default_mismatches.append(
                        f"{table_name}.{model_col.name}: model_default='{model_default}' db_default='{db_default}'"
                    )

        model_indexes = _model_index_signature(table)
        db_indexes = _db_index_signature(inspector, table_name)
        if db_indexes and model_indexes != db_indexes:
            index_mismatches.append(
                f"{table_name}: missing={sorted(model_indexes - db_indexes)} extra={sorted(db_indexes - model_indexes)}"
            )

        model_uniques = _model_unique_signature(table)
        db_uniques = _db_unique_signature(inspector, table_name)
        if db_uniques and model_uniques != db_uniques:
            unique_mismatches.append(
                f"{table_name}: missing={sorted(model_uniques - db_uniques)} extra={sorted(db_uniques - model_uniques)}"
            )

        model_fks = _model_fk_signature(table)
        db_fks = _db_fk_signature(inspector, table_name)
        if db_fks and model_fks != db_fks:
            fk_mismatches.append(
                f"{table_name}: missing={sorted(model_fks - db_fks)} extra={sorted(db_fks - model_fks)}"
            )

    if column_mismatches:
        errors.append("column parity mismatch: " + "; ".join(column_mismatches))
    if nullable_mismatches:
        errors.append("nullable parity mismatch: " + "; ".join(nullable_mismatches))
    if type_mismatches:
        errors.append("type parity mismatch: " + "; ".join(type_mismatches))
    if default_mismatches:
        errors.append("default parity mismatch: " + "; ".join(default_mismatches))
    if index_mismatches:
        errors.append("index parity mismatch: " + "; ".join(index_mismatches))
    if unique_mismatches:
        errors.append("unique constraint parity mismatch: " + "; ".join(unique_mismatches))
    if fk_mismatches:
        errors.append("foreign key parity mismatch: " + "; ".join(fk_mismatches))

    return errors


def main() -> int:
    with tempfile.NamedTemporaryFile(prefix="schema_parity_", suffix=".db") as temp_db:
        database_url = f"sqlite+pysqlite:///{temp_db.name}"
        _upgrade_schema(database_url)
        engine = create_engine(database_url, future=True)
        inspector = inspect(engine)

        model_tables = set(Base.metadata.tables.keys())
        db_tables = {name for name in inspector.get_table_names() if name != "alembic_version"}
        errors = collect_schema_parity_errors(inspector)

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
