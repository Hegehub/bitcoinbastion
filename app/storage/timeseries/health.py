"""TimescaleDB health checks for the storage status endpoint."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.storage.schemas import StorageRole, StorageStatusValue, StorageStoreStatus


def _latency_ms(started_at: float) -> float:
    return round((time.monotonic() - started_at) * 1000, 3)


def _safe_error_details(exc: BaseException, *, schema: str) -> dict[str, Any]:
    return {
        "connection": "failed",
        "error_class": type(exc).__name__,
        "schema": schema,
        "extension_available": False,
        "hypertables": {},
    }


def _market_hypertable_status(db: Session) -> dict[str, bool]:
    expected = {
        "btc_price_points": False,
        "btc_candles": False,
        "mempool_fee_snapshots": False,
    }
    rows = db.execute(text("""
            SELECT hypertable_name
            FROM timescaledb_information.hypertables
            WHERE hypertable_schema = 'public'
              AND hypertable_name IN ('btc_price_points', 'btc_candles', 'mempool_fee_snapshots')
            """)).fetchall()
    for row in rows:
        expected[str(row[0])] = True
    return expected


def check_timescale(settings: Settings, db: Session) -> StorageStoreStatus:
    """Return sanitized TimescaleDB health for the operational storage endpoint."""

    schema = settings.timescale_schema
    purpose = "time-series, candles, metrics, provider health"

    if not settings.timescale_enabled:
        return StorageStoreStatus(
            status=StorageStatusValue.DISABLED,
            role=StorageRole.FUTURE,
            purpose=purpose,
            details={
                "reason": "TIMESCALE_ENABLED=false",
                "enabled": False,
                "schema": schema,
                "extension_available": None,
                "hypertables": {},
            },
        )

    bind = db.get_bind()
    dialect_name = getattr(getattr(bind, "dialect", None), "name", "unknown")
    if dialect_name not in {"postgresql", "postgres"}:
        return StorageStoreStatus(
            status=StorageStatusValue.DEGRADED,
            role=StorageRole.FUTURE,
            purpose=purpose,
            details={
                "enabled": True,
                "schema": schema,
                "extension_available": False,
                "hypertables": {},
                "reason": "TimescaleDB health requires a PostgreSQL-compatible connection",
            },
        )

    started_at = time.monotonic()
    try:
        row = db.execute(text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_extension
                    WHERE extname = 'timescaledb'
                ) AS extension_available
                """)).first()
        extension_available = bool(row[0]) if row is not None else False
        hypertables = _market_hypertable_status(db) if extension_available else {}
    except SQLAlchemyError as exc:
        return StorageStoreStatus(
            status=StorageStatusValue.UNAVAILABLE,
            role=StorageRole.FUTURE,
            purpose=purpose,
            latency_ms=_latency_ms(started_at),
            details=_safe_error_details(exc, schema=schema),
        )
    except Exception as exc:  # noqa: BLE001 - operational health must be sanitized.
        return StorageStoreStatus(
            status=StorageStatusValue.UNAVAILABLE,
            role=StorageRole.FUTURE,
            purpose=purpose,
            latency_ms=_latency_ms(started_at),
            details=_safe_error_details(exc, schema=schema),
        )

    return StorageStoreStatus(
        status=StorageStatusValue.OK if extension_available else StorageStatusValue.DEGRADED,
        role=StorageRole.FUTURE,
        purpose=purpose,
        latency_ms=_latency_ms(started_at),
        details={
            "enabled": True,
            "schema": schema,
            "extension_available": extension_available,
            "hypertables": hypertables,
            "create_extension": settings.timescale_create_extension,
            "default_chunk_interval": settings.timescale_default_chunk_interval,
        },
    )
