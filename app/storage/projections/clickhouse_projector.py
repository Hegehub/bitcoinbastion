"""Outbox-to-ClickHouse projection worker.

ClickHouse is a rebuildable analytics projection store. Canonical truth remains in
PostgreSQL, TimescaleDB, and Object Storage. This projector never treats a
successful ClickHouse insert as canonical business state.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import Settings
from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.db.repositories.storage_outbox_repository import StorageOutboxRepository
from app.storage.analytics_store.base import AnalyticsStore
from app.storage.analytics_store.errors import (
    AnalyticsStoreDisabledError,
    AnalyticsStoreError,
    AnalyticsStoreInsertError,
)
from app.storage.outbox.enums import StorageOutboxTargetStore
from app.storage.projections.schemas import ClickHouseProjectionSummary

logger = logging.getLogger(__name__)

CLICKHOUSE_TARGET_STORE = StorageOutboxTargetStore.CLICKHOUSE.value

SUPPORTED_EVENT_TABLES: dict[str, str] = {
    "market.time_machine.event": "market_time_machine_events",
    "news.impact.event": "news_impact_events",
    "candle.attribution.event": "candle_attribution_events",
    "trace.runtime.event": "trace_runtime_events",
    "webhook.delivery.event": "webhook_delivery_events",
    "api.usage.event": "api_usage_events",
    "operator.replay.event": "operator_replay_events",
    "provider.health.event": "operator_replay_events",
}

FORBIDDEN_PAYLOAD_TOKENS = (
    "seed",
    "seed_phrase",
    "mnemonic",
    "private_key",
    "wallet_file",
    "wallet.dat",
    "xprv",
    "yprv",
    "zprv",
    "api_key",
    "access_token",
    "access_pass_token",
    "session_token",
    "authorization",
    "signature",
    "payment_secret",
    "recovery_seed",
)


class ClickHouseProjectionError(RuntimeError):
    """Base projector error with sanitized messages."""


class UnsupportedEventTypeError(ClickHouseProjectionError):
    """Raised for outbox events without a ClickHouse mapping."""


class InvalidProjectionPayloadError(ClickHouseProjectionError):
    """Raised for malformed or unsafe outbox payloads."""


class ProjectionMappingError(ClickHouseProjectionError):
    """Raised when a safe payload cannot be mapped to a ClickHouse row."""


@dataclass(frozen=True)
class ProjectedClickHouseRow:
    table: str
    row: dict[str, object]
    projection_id: str


class ClickHouseOutboxProjector:
    def __init__(
        self,
        *,
        settings: Settings,
        outbox_repository: StorageOutboxRepository,
        analytics_store: AnalyticsStore,
        worker_id: str = "storage-clickhouse-projector",
    ) -> None:
        self.settings = settings
        self.outbox_repository = outbox_repository
        self.analytics_store = analytics_store
        self.worker_id = worker_id

    async def project_batch(
        self,
        *,
        batch_size: int = 100,
        event_type: str | None = None,
        max_runtime_seconds: int | None = 30,
        dry_run: bool = False,
    ) -> ClickHouseProjectionSummary:
        if not self.settings.storage.clickhouse.enabled:
            return ClickHouseProjectionSummary(
                clickhouse_enabled=False,
                dry_run=dry_run,
                reason="clickhouse_disabled",
            )

        started_at = time.monotonic()
        summary = ClickHouseProjectionSummary(dry_run=dry_run, clickhouse_enabled=True)
        events = self._fetch_events(batch_size=batch_size, event_type=event_type, dry_run=dry_run)
        for event in events:
            if _timed_out(started_at, max_runtime_seconds):
                summary.reason = "max_runtime_seconds_reached"
                break
            await self._project_one(event, summary=summary, dry_run=dry_run)
        return summary

    def _fetch_events(
        self,
        *,
        batch_size: int,
        event_type: str | None,
        dry_run: bool,
    ) -> list[StorageOutboxEvent]:
        if dry_run:
            return self.outbox_repository.list_projectable_events(
                target_store=CLICKHOUSE_TARGET_STORE,
                limit=batch_size,
                event_type=event_type,
            )
        return self.outbox_repository.claim_projectable_events(
            target_store=CLICKHOUSE_TARGET_STORE,
            worker_id=self.worker_id,
            limit=batch_size,
            event_type=event_type,
        )

    async def _project_one(
        self,
        event: StorageOutboxEvent,
        *,
        summary: ClickHouseProjectionSummary,
        dry_run: bool,
    ) -> None:
        summary.processed += 1
        log_fields = _safe_log_fields(event, self.worker_id)
        try:
            projected = map_outbox_event_to_clickhouse_row(event)
            if dry_run:
                summary.skipped += 1
                logger.info(
                    "clickhouse_projection_dry_run", extra={**log_fields, "table": projected.table}
                )
                return
            result = await self.analytics_store.insert_events(projected.table, [projected.row])
            summary.inserted += result.inserted_count
            self.outbox_repository.mark_processed(event.event_id)
            logger.info(
                "clickhouse_projection_processed",
                extra={**log_fields, "table": projected.table, "projection_status": "processed"},
            )
        except UnsupportedEventTypeError as exc:
            summary.failed_terminal += 1
            self._record_terminal(event, exc, dry_run=dry_run)
        except InvalidProjectionPayloadError as exc:
            summary.failed_terminal += 1
            self._record_terminal(event, exc, dry_run=dry_run)
        except ProjectionMappingError as exc:
            summary.failed_terminal += 1
            self._record_terminal(event, exc, dry_run=dry_run)
        except (AnalyticsStoreDisabledError, AnalyticsStoreInsertError, AnalyticsStoreError) as exc:
            summary.failed_retryable += 1
            self._record_retryable(event, exc, dry_run=dry_run)
        except Exception as exc:  # noqa: BLE001 - projectors must surface sanitized failures.
            summary.failed_retryable += 1
            self._record_retryable(event, exc, dry_run=dry_run)

    def _record_terminal(
        self, event: StorageOutboxEvent, exc: BaseException, *, dry_run: bool
    ) -> None:
        if dry_run:
            return
        self.outbox_repository.mark_failed(event.event_id, _sanitize_error(exc))
        logger.warning(
            "clickhouse_projection_terminal_failure",
            extra={
                **_safe_log_fields(event, self.worker_id),
                "projection_status": "failed_terminal",
            },
        )

    def _record_retryable(
        self, event: StorageOutboxEvent, exc: BaseException, *, dry_run: bool
    ) -> None:
        if dry_run:
            return
        self.outbox_repository.mark_retry(
            event.event_id,
            _sanitize_error(exc),
            datetime.now(UTC),
        )
        logger.warning(
            "clickhouse_projection_retryable_failure",
            extra={
                **_safe_log_fields(event, self.worker_id),
                "projection_status": "failed_retryable",
            },
        )


def map_outbox_event_to_clickhouse_row(event: StorageOutboxEvent) -> ProjectedClickHouseRow:
    table = SUPPORTED_EVENT_TABLES.get(event.event_type)
    if table is None:
        raise UnsupportedEventTypeError("unsupported_event_type")
    payload = _require_payload(event.payload_json)
    metadata = _require_metadata(event.metadata_json)
    _validate_no_sensitive_payload(payload)
    _validate_no_sensitive_payload(metadata)

    projection_id = build_projection_id(event)
    now = _iso_utc()
    occurred_at = str(payload.get("occurred_at") or event.created_at.isoformat())
    row: dict[str, object] = {
        "event_id": projection_id,
        "occurred_at": occurred_at,
        "ingested_at": str(payload.get("ingested_at") or now),
        "source_store": str(metadata.get("source_store") or "storage_outbox"),
        "source_table": str(metadata.get("source_table") or event.aggregate_type),
        "source_id_hash": str(payload.get("source_id_hash") or _hash_value(event.aggregate_id)),
        "projection_version": int(metadata.get("projection_version") or 1),
        "schema_version": int(metadata.get("schema_version") or 1),
        "created_at": now,
        "payload_json": _safe_payload_json(payload),
    }
    row.update(_table_defaults(table, event, payload))
    row.update(
        {
            key: value
            for key, value in payload.items()
            if key not in row and _is_projection_safe_value(value)
        }
    )
    return ProjectedClickHouseRow(table=table, row=row, projection_id=projection_id)


def build_projection_id(event: StorageOutboxEvent) -> str:
    raw = "|".join([event.event_type, event.aggregate_type, event.aggregate_id, event.event_id])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _table_defaults(
    table: str, event: StorageOutboxEvent, payload: Mapping[str, object]
) -> dict[str, object]:
    common_hash = _hash_value(event.aggregate_id)
    if table == "market_time_machine_events":
        return {
            "event_type": event.event_type,
            "asset": str(payload.get("asset") or "btc"),
            "market_venue": str(payload.get("market_venue") or "unknown"),
            "timeframe": str(payload.get("timeframe") or "unknown"),
            "regime": str(payload.get("regime") or "unknown"),
            "confidence_band": str(payload.get("confidence_band") or "unknown"),
            "signal_family": str(payload.get("signal_family") or "unknown"),
            "correlation_id_hash": str(payload.get("correlation_id_hash") or common_hash),
        }
    if table == "news_impact_events":
        return {
            "news_article_hash": str(payload.get("news_article_hash") or common_hash),
            "news_event_hash": str(payload.get("news_event_hash") or common_hash),
            "source_hash": str(payload.get("source_hash") or common_hash),
            "source_tier": str(payload.get("source_tier") or "unknown"),
            "narrative_tags": list(payload.get("narrative_tags") or []),
            "asset": str(payload.get("asset") or "btc"),
            "impact_window": str(payload.get("impact_window") or "unknown"),
            "sentiment_band": str(payload.get("sentiment_band") or "unknown"),
        }
    if table == "candle_attribution_events":
        return {
            "candle_hash": str(payload.get("candle_hash") or common_hash),
            "asset": str(payload.get("asset") or "btc"),
            "timeframe": str(payload.get("timeframe") or "unknown"),
            "candle_open_time": str(
                payload.get("candle_open_time") or payload.get("occurred_at") or _iso_utc()
            ),
            "candidate_type": str(payload.get("candidate_type") or "unknown"),
            "candidate_hash": str(payload.get("candidate_hash") or common_hash),
            "candidate_rank": int(payload.get("candidate_rank") or 0),
            "explanation_hash": str(payload.get("explanation_hash") or common_hash),
            "limitations": list(payload.get("limitations") or []),
        }
    if table == "trace_runtime_events":
        return {
            "trace_event_type": event.event_type,
            "report_hash": str(payload.get("report_hash") or common_hash),
            "address_hash": str(payload.get("address_hash") or common_hash),
            "workspace_id_hash": str(payload.get("workspace_id_hash") or common_hash),
            "risk_band": str(payload.get("risk_band") or "unknown"),
            "confidence_band": str(payload.get("confidence_band") or "unknown"),
            "provider_count": int(payload.get("provider_count") or 0),
            "disagreement_band": str(payload.get("disagreement_band") or "unknown"),
            "privacy_exposure_band": str(payload.get("privacy_exposure_band") or "unknown"),
            "review_status": str(payload.get("review_status") or "unknown"),
        }
    if table == "webhook_delivery_events":
        return {
            "webhook_endpoint_hash": str(payload.get("webhook_endpoint_hash") or common_hash),
            "workspace_id_hash": str(payload.get("workspace_id_hash") or common_hash),
            "event_type": event.event_type,
            "delivery_status": str(payload.get("delivery_status") or "unknown"),
            "attempt_number": int(payload.get("attempt_number") or 1),
            "error_class": str(payload.get("error_class") or "none"),
        }
    if table == "api_usage_events":
        return {
            "client_type": str(payload.get("client_type") or "unknown"),
            "api_surface": str(payload.get("api_surface") or "api"),
            "endpoint_family": str(payload.get("endpoint_family") or "unknown"),
            "method": str(payload.get("method") or "unknown"),
            "status_family": str(payload.get("status_family") or "unknown"),
            "plan_code": str(payload.get("plan_code") or "unknown"),
            "workspace_id_hash": str(payload.get("workspace_id_hash") or common_hash),
            "pass_lookup_hash": str(payload.get("pass_lookup_hash") or common_hash),
            "api_key_hash": str(payload.get("api_key_hash") or common_hash),
            "session_id_hash": str(payload.get("session_id_hash") or common_hash),
            "rate_limited": int(payload.get("rate_limited") or 0),
            "policy_decision": str(payload.get("policy_decision") or "unknown"),
        }
    return {
        "operator_event_type": event.event_type,
        "actor_hash": str(payload.get("actor_hash") or common_hash),
        "workspace_id_hash": str(payload.get("workspace_id_hash") or common_hash),
        "object_hash": str(payload.get("object_hash") or common_hash),
        "object_type": str(payload.get("object_type") or event.aggregate_type),
        "decision": str(payload.get("decision") or "unknown"),
        "risk_band": str(payload.get("risk_band") or "unknown"),
        "policy_version_hash": str(payload.get("policy_version_hash") or common_hash),
        "audit_event_hash": str(payload.get("audit_event_hash") or common_hash),
    }


def _require_payload(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise InvalidProjectionPayloadError("invalid_payload")
    return payload


def _require_metadata(metadata: object) -> Mapping[str, object]:
    if not isinstance(metadata, Mapping):
        return {}
    return metadata


def _validate_no_sensitive_payload(value: object) -> None:
    flattened = json.dumps(value, sort_keys=True, default=str).casefold()
    if any(token in flattened for token in FORBIDDEN_PAYLOAD_TOKENS):
        raise InvalidProjectionPayloadError("invalid_payload_sensitive_material")


def _safe_payload_json(payload: Mapping[str, object]) -> str:
    safe_payload = {
        key: value
        for key, value in payload.items()
        if _is_projection_safe_value(value) and not _contains_forbidden_token(key)
    }
    return json.dumps(safe_payload, sort_keys=True, default=str)


def _is_projection_safe_value(value: object) -> bool:
    if isinstance(value, str):
        return not _contains_forbidden_token(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return True
    if isinstance(value, list):
        return all(_is_projection_safe_value(item) for item in value)
    if isinstance(value, Mapping):
        return not any(_contains_forbidden_token(str(key)) for key in value)
    return False


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.casefold()
    return any(token in lowered for token in FORBIDDEN_PAYLOAD_TOKENS)


def _hash_value(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _iso_utc() -> str:
    return datetime.now(UTC).isoformat()


def _sanitize_error(exc: BaseException) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if _contains_forbidden_token(message) or "sensitive_material" in message.casefold():
        return "[REDACTED]"
    return message[:500]


def _safe_log_fields(event: StorageOutboxEvent, worker_id: str) -> dict[str, object]:
    return {
        "event_type": event.event_type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id_hash": _hash_value(event.aggregate_id),
        "outbox_event_id": event.event_id,
        "target_store": CLICKHOUSE_TARGET_STORE,
        "retry_count": event.retry_count,
        "worker_id": worker_id,
    }


def _timed_out(started_at: float, max_runtime_seconds: int | None) -> bool:
    if max_runtime_seconds is None:
        return False
    return (time.monotonic() - started_at) >= max_runtime_seconds


def project_batch_sync(
    projector: ClickHouseOutboxProjector, **kwargs: object
) -> ClickHouseProjectionSummary:
    return asyncio.run(projector.project_batch(**kwargs))
