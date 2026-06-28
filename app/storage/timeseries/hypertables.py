"""Safe TimescaleDB extension and hypertable helpers.

These helpers prepare SQL for future TimescaleDB-backed repositories. They do not
migrate existing domain tables and they intentionally validate all identifiers
before SQL is constructed.
"""

from __future__ import annotations

import inspect
import re
from typing import Any

from sqlalchemy import text

from app.storage.timeseries.errors import TimescaleConfigurationError, TimescaleHypertableError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INTERVAL_RE = re.compile(
    r"^[1-9][0-9]*\s+(microsecond|microseconds|millisecond|milliseconds|second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)$"
)


def validate_identifier(identifier: str, *, label: str = "identifier") -> str:
    candidate = identifier.strip()
    if not _IDENTIFIER_RE.fullmatch(candidate):
        raise TimescaleConfigurationError(f"Invalid TimescaleDB {label}.")
    return candidate


def validate_table_name(table_name: str) -> str:
    parts = [part.strip() for part in table_name.split(".")]
    if len(parts) not in {1, 2} or any(not part for part in parts):
        raise TimescaleConfigurationError("Invalid TimescaleDB table name.")
    return ".".join(validate_identifier(part, label="table name") for part in parts)


def validate_interval(interval: str, *, label: str = "interval") -> str:
    candidate = " ".join(interval.strip().split())
    if not _INTERVAL_RE.fullmatch(candidate):
        raise TimescaleConfigurationError(f"Invalid TimescaleDB {label}.")
    return candidate


def _quote_identifier(identifier: str) -> str:
    return '"' + validate_identifier(identifier).replace('"', '""') + '"'


def _regclass_literal(table_name: str) -> str:
    validated = validate_table_name(table_name)
    return ".".join(_quote_identifier(part) for part in validated.split("."))


async def _execute(conn: Any, statement: Any, parameters: dict[str, Any] | None = None) -> Any:
    try:
        result = conn.execute(statement, parameters or {})
        if inspect.isawaitable(result):
            return await result
        return result
    except TimescaleConfigurationError:
        raise
    except Exception as exc:  # noqa: BLE001 - wrap without exposing connection details.
        raise TimescaleHypertableError(type(exc).__name__) from exc


async def ensure_timescale_extension(conn: Any) -> None:
    """Create the TimescaleDB extension idempotently on PostgreSQL/TimescaleDB."""

    await _execute(conn, text("CREATE EXTENSION IF NOT EXISTS timescaledb"))


async def create_hypertable_if_not_exists(
    conn: Any,
    table_name: str,
    time_column: str,
    chunk_interval: str | None = None,
    if_not_exists: bool = True,
) -> None:
    """Create a hypertable for a validated table/time column if needed."""

    regclass = _regclass_literal(table_name)
    column = validate_identifier(time_column, label="time column")
    interval = validate_interval(chunk_interval, label="chunk interval") if chunk_interval else None

    statement = """
        SELECT create_hypertable(
            :table_name,
            :time_column,
            if_not_exists => :if_not_exists{chunk_clause}
        )
    """.format(
        chunk_clause=(
            ", chunk_time_interval => CAST(:chunk_interval AS INTERVAL)" if interval else ""
        )
    )
    params: dict[str, Any] = {
        "table_name": regclass,
        "time_column": column,
        "if_not_exists": if_not_exists,
    }
    if interval:
        params["chunk_interval"] = interval
    await _execute(conn, text(statement), params)


async def set_compression_policy(conn: Any, table_name: str, compress_after: str) -> None:
    """Enable compression policy for a validated hypertable."""

    regclass = _regclass_literal(table_name)
    interval = validate_interval(compress_after, label="compression interval")
    await _execute(
        conn,
        text(
            "SELECT add_compression_policy(:table_name, CAST(:compress_after AS INTERVAL), if_not_exists => true)"
        ),
        {"table_name": regclass, "compress_after": interval},
    )


async def set_retention_policy(conn: Any, table_name: str, drop_after: str) -> None:
    """Enable retention policy for a validated hypertable."""

    regclass = _regclass_literal(table_name)
    interval = validate_interval(drop_after, label="retention interval")
    await _execute(
        conn,
        text(
            "SELECT add_retention_policy(:table_name, CAST(:drop_after AS INTERVAL), if_not_exists => true)"
        ),
        {"table_name": regclass, "drop_after": interval},
    )
