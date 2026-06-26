"""Storage status checks for the operational Storage Health API."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from redis import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.storage.analytics_store.health import check_analytics_store
from app.storage.analytics_store.schemas import AnalyticsStoreStatusValue
from app.storage.object_store.client import DisabledObjectStore, ObjectStoreHealthCheck
from app.storage.object_store.local_store import LocalObjectStore
from app.storage.timeseries.health import check_timescale
from app.storage.schemas import (
    StorageDegradedMode,
    StorageRole,
    StorageStatusResponse,
    StorageStatusSummary,
    StorageStatusValue,
    StorageStoreStatus,
)

STORE_POSTGRES = "postgres"
STORE_REDIS = "redis"
STORE_OBJECT_STORAGE = "object_storage"
STORE_TIMESCALE = "timescale"
STORE_CLICKHOUSE = "clickhouse"
STORE_QDRANT = "qdrant"
STORE_SQLITE_LOCAL = "sqlite_local"
STORE_DUCKDB_LOCAL = "duckdb_local"

EXPECTED_STORE_ORDER = (
    STORE_POSTGRES,
    STORE_REDIS,
    STORE_OBJECT_STORAGE,
    STORE_TIMESCALE,
    STORE_CLICKHOUSE,
    STORE_QDRANT,
    STORE_SQLITE_LOCAL,
    STORE_DUCKDB_LOCAL,
)

PRODUCTION_LIKE_PROFILES = {"staging", "production", "enterprise", "air_gapped"}


def _latency_ms(started_at: float) -> float:
    return round((time.monotonic() - started_at) * 1000, 3)


def _safe_error_details(exc: BaseException) -> dict[str, str]:
    return {"connection": "failed", "error_class": type(exc).__name__}


def check_postgres(db: Session) -> StorageStoreStatus:
    started_at = time.monotonic()
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return StorageStoreStatus(
            status=StorageStatusValue.UNAVAILABLE,
            role=StorageRole.REQUIRED,
            purpose="transactional source of truth",
            latency_ms=_latency_ms(started_at),
            details=_safe_error_details(exc),
        )
    except Exception as exc:  # noqa: BLE001 - operational endpoint sanitizes unexpected failures.
        return StorageStoreStatus(
            status=StorageStatusValue.UNAVAILABLE,
            role=StorageRole.REQUIRED,
            purpose="transactional source of truth",
            latency_ms=_latency_ms(started_at),
            details=_safe_error_details(exc),
        )
    return StorageStoreStatus(
        status=StorageStatusValue.OK,
        role=StorageRole.REQUIRED,
        purpose="transactional source of truth",
        latency_ms=_latency_ms(started_at),
        details={"connection": "ok"},
    )


def check_redis(settings: Settings, redis_client_factory: Callable[[], Any]) -> StorageStoreStatus:
    if not settings.redis_url.strip():
        return StorageStoreStatus(
            status=StorageStatusValue.NOT_CONFIGURED,
            role=StorageRole.REQUIRED,
            purpose="cache, rate limits, queues, short-lived runtime state",
            details={"reason": "REDIS_URL is not configured"},
        )

    started_at = time.monotonic()
    try:
        redis_client_factory().ping()
    except RedisError as exc:
        return StorageStoreStatus(
            status=StorageStatusValue.UNAVAILABLE,
            role=StorageRole.REQUIRED,
            purpose="cache, rate limits, queues, short-lived runtime state",
            latency_ms=_latency_ms(started_at),
            details=_safe_error_details(exc),
        )
    except Exception as exc:  # noqa: BLE001 - health response must be sanitized.
        return StorageStoreStatus(
            status=StorageStatusValue.UNAVAILABLE,
            role=StorageRole.REQUIRED,
            purpose="cache, rate limits, queues, short-lived runtime state",
            latency_ms=_latency_ms(started_at),
            details=_safe_error_details(exc),
        )
    return StorageStoreStatus(
        status=StorageStatusValue.OK,
        role=StorageRole.REQUIRED,
        purpose="cache, rate limits, queues, short-lived runtime state",
        latency_ms=_latency_ms(started_at),
        details={"connection": "ok", "ephemeral_only": settings.redis_ephemeral_only},
    )


async def check_object_storage(settings: Settings) -> StorageStoreStatus:
    storage = settings.storage.object_storage
    required = _object_storage_required(settings)
    role = StorageRole.REQUIRED if required else StorageRole.OPTIONAL
    purpose = "proof packets, evidence artifacts, signed archives"

    if not storage.enabled:
        return StorageStoreStatus(
            status=StorageStatusValue.DISABLED,
            role=role,
            purpose=purpose,
            details={"reason": "OBJECT_STORAGE_ENABLED=false"},
        )

    if not storage.bucket.strip():
        return StorageStoreStatus(
            status=StorageStatusValue.MISCONFIGURED,
            role=role,
            purpose=purpose,
            details={"bucket": "missing"},
        )

    if storage.backend == "local":
        check = ObjectStoreHealthCheck(
            LocalObjectStore(storage.local_root, storage.max_object_bytes),
            bucket=storage.bucket,
            enabled=True,
        )
        result = await check.check_health()
        return StorageStoreStatus(
            status=StorageStatusValue(result.status),
            role=role,
            purpose=purpose,
            latency_ms=result.latency_ms,
            details={
                "backend": "local",
                "bucket": storage.bucket,
                "read_check": "ok" if result.status == "ok" else "failed",
                "write_check": "ok" if result.status == "ok" else "failed",
            },
        )

    if storage.backend in {"minio", "s3", "compatible_s3"}:
        return StorageStoreStatus(
            status=StorageStatusValue.NOT_IMPLEMENTED,
            role=role,
            purpose=purpose,
            details={
                "backend": storage.backend,
                "bucket": storage.bucket,
                "reason": "remote object storage status check is not implemented in this prompt",
            },
        )

    check = ObjectStoreHealthCheck(DisabledObjectStore(), bucket=storage.bucket, enabled=False)
    result = await check.check_health()
    return StorageStoreStatus(
        status=StorageStatusValue(result.status),
        role=role,
        purpose=purpose,
        latency_ms=result.latency_ms,
        details={"backend": storage.backend, "reason": result.message or "disabled"},
    )


def _object_storage_required(settings: Settings) -> bool:
    return bool(
        settings.object_storage_enabled
        or (
            settings.storage_profile in PRODUCTION_LIKE_PROFILES
            and settings.storage_require_object_storage_in_production
        )
    )


def future_store_status(
    *,
    enabled: bool,
    store: str,
    purpose: str,
    reason: str,
) -> StorageStoreStatus:
    if enabled:
        return StorageStoreStatus(
            status=StorageStatusValue.NOT_IMPLEMENTED,
            role=StorageRole.FUTURE,
            purpose=purpose,
            details={"reason": f"{store} is enabled but no client is implemented in this prompt"},
        )
    return StorageStoreStatus(
        status=StorageStatusValue.DISABLED,
        role=StorageRole.FUTURE,
        purpose=purpose,
        details={"reason": reason},
    )


def local_store_status(*, enabled: bool, purpose: str, reason: str) -> StorageStoreStatus:
    if enabled:
        return StorageStoreStatus(
            status=StorageStatusValue.NOT_IMPLEMENTED,
            role=StorageRole.LOCAL_ONLY,
            purpose=purpose,
            details={"reason": "local storage status check is not implemented in this prompt"},
        )
    return StorageStoreStatus(
        status=StorageStatusValue.DISABLED,
        role=StorageRole.LOCAL_ONLY,
        purpose=purpose,
        details={"reason": reason},
    )


async def collect_storage_status(
    *,
    settings: Settings,
    db: Session,
    redis_client_factory: Callable[[], Any],
) -> StorageStatusResponse:
    stores = {
        STORE_POSTGRES: check_postgres(db),
        STORE_REDIS: check_redis(settings, redis_client_factory),
        STORE_OBJECT_STORAGE: await check_object_storage(settings),
        STORE_TIMESCALE: check_timescale(settings, db),
        STORE_CLICKHOUSE: _clickhouse_store_status(await check_analytics_store(settings)),
        STORE_QDRANT: future_store_status(
            enabled=settings.qdrant_enabled,
            store=STORE_QDRANT,
            purpose="semantic memory, similarity, narrative search",
            reason="QDRANT_ENABLED=false",
        ),
        STORE_SQLITE_LOCAL: local_store_status(
            enabled=settings.local_storage_enabled,
            purpose="local operational DB for Desktop AI / PayRegister / offline mode",
            reason="LOCAL_STORAGE_ENABLED=false",
        ),
        STORE_DUCKDB_LOCAL: local_store_status(
            enabled=settings.local_storage_enabled,
            purpose="local analytics, exports, offline reports",
            reason="LOCAL_STORAGE_ENABLED=false",
        ),
    }
    ordered_stores = {name: stores[name] for name in EXPECTED_STORE_ORDER}
    status, summary, degraded_mode = _summarize(ordered_stores)
    return StorageStatusResponse(
        status=status,
        profile=settings.storage_profile,
        summary=summary,
        stores=ordered_stores,
        degraded_mode=degraded_mode,
    )


def _clickhouse_store_status(health: Any) -> StorageStoreStatus:
    status_map = {
        AnalyticsStoreStatusValue.OK: StorageStatusValue.OK,
        AnalyticsStoreStatusValue.DISABLED: StorageStatusValue.DISABLED,
        AnalyticsStoreStatusValue.DEGRADED: StorageStatusValue.DEGRADED,
        AnalyticsStoreStatusValue.UNAVAILABLE: StorageStatusValue.UNAVAILABLE,
        AnalyticsStoreStatusValue.MISCONFIGURED: StorageStatusValue.MISCONFIGURED,
        AnalyticsStoreStatusValue.UNKNOWN: StorageStatusValue.UNKNOWN,
    }
    details = {
        "enabled": health.enabled,
        "database": health.database,
        "error": health.error,
        **health.details,
    }
    return StorageStoreStatus(
        status=status_map.get(health.status, StorageStatusValue.UNKNOWN),
        role=StorageRole.FUTURE,
        purpose="analytics warehouse, Market Time Machine, replay",
        latency_ms=health.latency_ms,
        details=details,
    )


def collect_storage_status_sync(
    *,
    settings: Settings,
    db: Session,
    redis_client_factory: Callable[[], Any],
) -> StorageStatusResponse:
    return asyncio.run(
        collect_storage_status(
            settings=settings,
            db=db,
            redis_client_factory=redis_client_factory,
        )
    )


def _summarize(
    stores: dict[str, StorageStoreStatus],
) -> tuple[StorageStatusValue, StorageStatusSummary, StorageDegradedMode]:
    failure_statuses = {
        StorageStatusValue.UNAVAILABLE,
        StorageStatusValue.MISCONFIGURED,
        StorageStatusValue.NOT_CONFIGURED,
        StorageStatusValue.NOT_IMPLEMENTED,
        StorageStatusValue.DISABLED,
    }
    degraded_statuses = {
        StorageStatusValue.DEGRADED,
        StorageStatusValue.UNAVAILABLE,
        StorageStatusValue.MISCONFIGURED,
        StorageStatusValue.NOT_CONFIGURED,
        StorageStatusValue.NOT_IMPLEMENTED,
        StorageStatusValue.DISABLED,
        StorageStatusValue.UNKNOWN,
    }

    required_failures = [
        name
        for name, store in stores.items()
        if store.role == StorageRole.REQUIRED and store.status in failure_statuses
    ]
    optional_or_future_warnings = [
        name
        for name, store in stores.items()
        if store.role in {StorageRole.OPTIONAL, StorageRole.FUTURE}
        and store.status in degraded_statuses
    ]
    enabled_local_warnings = [
        name
        for name, store in stores.items()
        if store.role == StorageRole.LOCAL_ONLY
        and store.status == StorageStatusValue.NOT_IMPLEMENTED
    ]

    if required_failures:
        status = StorageStatusValue.UNAVAILABLE
        reason = "required_store_unavailable_or_misconfigured"
    elif optional_or_future_warnings:
        status = StorageStatusValue.DEGRADED
        reason = "optional_store_disabled_or_unavailable"
    else:
        status = StorageStatusValue.OK
        reason = None

    impact = _impact_for_stores(
        required_failures + optional_or_future_warnings + enabled_local_warnings
    )
    summary = StorageStatusSummary(
        required_ok=not required_failures,
        optional_degraded=bool(optional_or_future_warnings),
        critical_failures=len(required_failures),
        warnings=len(optional_or_future_warnings) + len(enabled_local_warnings),
    )
    degraded_mode = StorageDegradedMode(
        active=status != StorageStatusValue.OK or bool(enabled_local_warnings),
        reason=reason,
        impact=impact,
    )
    return status, summary, degraded_mode


def _impact_for_stores(store_names: list[str]) -> list[str]:
    impacts = {
        STORE_POSTGRES: "critical operations unavailable",
        STORE_REDIS: "cache, rate limits, queues, and websocket fanout may run in reduced mode",
        STORE_OBJECT_STORAGE: "proof packet downloads and evidence exports may be unavailable",
        STORE_TIMESCALE: "time-series metrics, candles, and provider health history may be unavailable",
        STORE_CLICKHOUSE: "Market Time Machine and long-range analytics may be unavailable",
        STORE_QDRANT: "semantic memory and similarity search may be unavailable",
        STORE_SQLITE_LOCAL: "local/offline operational features are not available",
        STORE_DUCKDB_LOCAL: "local analytics, exports, and offline reports are not available",
    }
    return [impacts[name] for name in EXPECTED_STORE_ORDER if name in store_names]
