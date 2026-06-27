from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.models.time_utils import utcnow
from app.db.repositories.provider_source_health_timeseries_repository import (
    ProviderSourceHealthTimeSeriesRepository,
)

FORBIDDEN_METADATA_TERMS = (
    "seed phrase",
    "mnemonic",
    "private key",
    "wallet.dat",
    "xprv",
    "yprv",
    "zprv",
    "secret",
    "token",
    "password",
    "authorization",
    "cookie",
    "access_key",
    "secret_key",
    "api_key",
    "bearer",
)


def _assert_safe_label(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty")
    lowered = cleaned.lower()
    if any(term in lowered for term in FORBIDDEN_METADATA_TERMS):
        raise ValueError(f"{field_name} contains sensitive material")
    if len(cleaned) > 120:
        raise ValueError(f"{field_name} must be 120 characters or fewer")
    return cleaned


def validate_safe_metadata(value: Any, path: str = "metadata_json") -> None:
    if value is None:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(term in key_text for term in FORBIDDEN_METADATA_TERMS):
                raise ValueError(f"{path}.{key} contains sensitive metadata")
            validate_safe_metadata(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_safe_metadata(item, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in FORBIDDEN_METADATA_TERMS):
            raise ValueError(f"{path} contains sensitive metadata")


class HealthSnapshotService:
    """Service boundary for provider/source health time-series observations."""

    def __init__(
        self,
        repository: ProviderSourceHealthTimeSeriesRepository,
        *,
        outbox: object | None = None,
    ) -> None:
        self.repository = repository
        self.outbox = outbox

    def record_provider_snapshot(
        self,
        *,
        provider_key: str,
        observed_at: datetime | None = None,
        source_key: str | None = None,
        source_type: str | None = None,
        domain: str = "generic",
        status: str = "ok",
        health_score: float | None = None,
        confidence_score: float | None = None,
        latency_ms: int | None = None,
        error_rate: float | None = None,
        success_count: int = 0,
        failure_count: int = 0,
        degraded_reason: str | None = None,
        runtime_mode: str = "normal",
        is_degraded: bool = False,
        metadata_json: dict[str, object] | None = None,
    ):
        metadata = metadata_json or {}
        validate_safe_metadata(metadata)
        snapshot = self.repository.record_provider_snapshot(
            observed_at=observed_at or utcnow(),
            provider_key=_assert_safe_label(provider_key, "provider_key"),
            source_key=_assert_safe_label(source_key, "source_key") if source_key else None,
            source_type=_assert_safe_label(source_type, "source_type") if source_type else None,
            domain=_assert_safe_label(domain, "domain"),
            status=_assert_safe_label(status, "status"),
            health_score=health_score,
            confidence_score=confidence_score,
            latency_ms=latency_ms,
            error_rate=error_rate,
            success_count=success_count,
            failure_count=failure_count,
            degraded_reason=degraded_reason[:255] if degraded_reason else None,
            runtime_mode=_assert_safe_label(runtime_mode, "runtime_mode"),
            is_degraded=is_degraded,
            metadata_json=metadata,
        )
        self._emit_provider_events(snapshot)
        return snapshot

    def record_source_snapshot(
        self,
        *,
        source_key: str,
        observed_at: datetime | None = None,
        provider_key: str | None = None,
        source_type: str | None = None,
        domain: str = "generic",
        status: str = "ok",
        health_score: float | None = None,
        confidence_score: float | None = None,
        latency_ms: int | None = None,
        error_rate: float | None = None,
        success_count: int = 0,
        failure_count: int = 0,
        degraded_reason: str | None = None,
        runtime_mode: str = "normal",
        is_degraded: bool = False,
        metadata_json: dict[str, object] | None = None,
    ):
        metadata = metadata_json or {}
        validate_safe_metadata(metadata)
        snapshot = self.repository.record_source_snapshot(
            observed_at=observed_at or utcnow(),
            provider_key=_assert_safe_label(provider_key, "provider_key") if provider_key else None,
            source_key=_assert_safe_label(source_key, "source_key"),
            source_type=_assert_safe_label(source_type, "source_type") if source_type else None,
            domain=_assert_safe_label(domain, "domain"),
            status=_assert_safe_label(status, "status"),
            health_score=health_score,
            confidence_score=confidence_score,
            latency_ms=latency_ms,
            error_rate=error_rate,
            success_count=success_count,
            failure_count=failure_count,
            degraded_reason=degraded_reason[:255] if degraded_reason else None,
            runtime_mode=_assert_safe_label(runtime_mode, "runtime_mode"),
            is_degraded=is_degraded,
            metadata_json=metadata,
        )
        self._emit_source_events(snapshot)
        return snapshot

    def record_provider_confidence_change(self, **values: Any):
        metadata = values.get("metadata_json") or {}
        validate_safe_metadata(metadata)
        values["metadata_json"] = metadata
        values["provider_key"] = _assert_safe_label(str(values["provider_key"]), "provider_key")
        values.setdefault("observed_at", utcnow())
        return self.repository.record_provider_confidence_event(**values)

    def record_source_confidence_change(self, **values: Any):
        metadata = values.get("metadata_json") or {}
        validate_safe_metadata(metadata)
        values["metadata_json"] = metadata
        values["source_key"] = _assert_safe_label(str(values["source_key"]), "source_key")
        values.setdefault("observed_at", utcnow())
        return self.repository.record_source_confidence_event(**values)

    def build_health_summary(self, from_ts: datetime, to_ts: datetime) -> dict[str, int]:
        return self.repository.health_summary(from_ts, to_ts)

    def _emit_provider_events(self, snapshot: object) -> None:
        if self.outbox is None:
            return
        payload = {
            "provider_key": getattr(snapshot, "provider_key"),
            "domain": getattr(snapshot, "domain"),
            "status": getattr(snapshot, "status"),
            "observed_at": getattr(snapshot, "observed_at").isoformat(),
            "is_degraded": bool(getattr(snapshot, "is_degraded")),
        }
        self.outbox.enqueue_event(
            event_type="provider.health.snapshot.recorded",
            aggregate_type="provider_health",
            aggregate_id=getattr(snapshot, "provider_key"),
            payload_json=payload,
            target_stores=["clickhouse", "audit"],
        )
        if getattr(snapshot, "is_degraded"):
            self.outbox.enqueue_event(
                event_type="provider.health.degraded",
                aggregate_type="provider_health",
                aggregate_id=getattr(snapshot, "provider_key"),
                payload_json=payload,
                target_stores=["clickhouse", "audit"],
            )
        elif getattr(snapshot, "status") == "recovered":
            self.outbox.enqueue_event(
                event_type="provider.health.recovered",
                aggregate_type="provider_health",
                aggregate_id=getattr(snapshot, "provider_key"),
                payload_json=payload,
                target_stores=["clickhouse", "audit"],
            )

    def _emit_source_events(self, snapshot: object) -> None:
        if self.outbox is None:
            return
        payload = {
            "source_key": getattr(snapshot, "source_key"),
            "domain": getattr(snapshot, "domain"),
            "status": getattr(snapshot, "status"),
            "observed_at": getattr(snapshot, "observed_at").isoformat(),
            "is_degraded": bool(getattr(snapshot, "is_degraded")),
        }
        self.outbox.enqueue_event(
            event_type="source.health.snapshot.recorded",
            aggregate_type="source_health",
            aggregate_id=getattr(snapshot, "source_key"),
            payload_json=payload,
            target_stores=["clickhouse", "audit"],
        )
        if getattr(snapshot, "is_degraded"):
            self.outbox.enqueue_event(
                event_type="source.health.degraded",
                aggregate_type="source_health",
                aggregate_id=getattr(snapshot, "source_key"),
                payload_json=payload,
                target_stores=["clickhouse", "audit"],
            )
        elif getattr(snapshot, "status") == "recovered":
            self.outbox.enqueue_event(
                event_type="source.health.recovered",
                aggregate_type="source_health",
                aggregate_id=getattr(snapshot, "source_key"),
                payload_json=payload,
                target_stores=["clickhouse", "audit"],
            )
