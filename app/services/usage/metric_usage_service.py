from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import uuid4

from app.db.models.metric_usage_event import MetricUsageEvent
from app.db.models.time_utils import utcnow
from app.services.usage.metric_usage_aggregates import build_usage_summary
from app.services.usage.metric_usage_models import MetricUsageEventCreate, MetricUsageSummary
from app.services.usage.metric_usage_repository import MetricUsageRepository, SubjectKind
from app.services.usage.metric_usage_safety import (
    FORBIDDEN_USAGE_TERMS,
    normalize_label,
    require_label,
    validate_safe_hash,
    validate_usage_metadata,
)


class MetricUsageOutbox(Protocol):
    def enqueue_event(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload_json: dict[str, object],
        target_stores: list[str],
    ) -> object: ...


class MetricUsageService:
    def __init__(
        self, repository: MetricUsageRepository, *, outbox: MetricUsageOutbox | None = None
    ) -> None:
        self.repository = repository
        self.outbox = outbox

    def record_usage_event(self, payload: MetricUsageEventCreate) -> MetricUsageEvent:
        event = self._build_event(payload)
        stored = self.repository.record_usage_event(event)
        self._emit_outbox_event(stored)
        return stored

    def record_many_usage_events(
        self, payloads: list[MetricUsageEventCreate]
    ) -> list[MetricUsageEvent]:
        events = [self._build_event(payload) for payload in payloads]
        stored = self.repository.record_many_usage_events(events)
        for event in stored:
            self._emit_outbox_event(event)
        return stored

    def get_usage_summary(self, from_ts: datetime, to_ts: datetime) -> MetricUsageSummary:
        return build_usage_summary(self.repository.get_usage_summary(from_ts, to_ts))

    def get_usage_by_metric_group(
        self, metric_group: str, from_ts: datetime, to_ts: datetime, limit: int = 100
    ) -> list[MetricUsageEvent]:
        normalized_group = require_label(metric_group, "metric_group", max_length=80)
        return self.repository.get_usage_by_metric_group(normalized_group, from_ts, to_ts, limit)

    def get_usage_by_subject(
        self,
        subject_kind: SubjectKind,
        subject_hash: str,
        from_ts: datetime,
        to_ts: datetime,
        limit: int = 100,
    ) -> list[MetricUsageEvent]:
        safe_hash = validate_safe_hash(subject_hash, f"{subject_kind}_hash")
        if safe_hash is None:
            raise ValueError("subject_hash is required")
        return self.repository.get_usage_by_subject(subject_kind, safe_hash, from_ts, to_ts, limit)

    def get_credit_consumption(
        self, from_ts: datetime, to_ts: datetime, *, metric_group: str | None = None
    ) -> int:
        normalized_group = normalize_label(metric_group, "metric_group", max_length=80)
        return self.repository.get_credit_consumption(from_ts, to_ts, metric_group=normalized_group)

    def get_denial_summary(self, from_ts: datetime, to_ts: datetime) -> dict[str, int]:
        return self.repository.get_denial_summary(from_ts, to_ts)

    def _build_event(self, payload: MetricUsageEventCreate) -> MetricUsageEvent:
        if payload.credit_cost < 0:
            raise ValueError("credit_cost must be non-negative")
        if payload.request_count < 1:
            raise ValueError("request_count must be at least 1")
        validate_usage_metadata(payload.metadata_json)
        return MetricUsageEvent(
            id=str(uuid4()),
            recorded_at=payload.recorded_at or utcnow(),
            event_type=require_label(payload.event_type, "event_type", max_length=80),
            decision=require_label(payload.decision, "decision", max_length=32),
            metric_group=normalize_label(payload.metric_group, "metric_group", max_length=80),
            metric_name=normalize_label(payload.metric_name, "metric_name", max_length=120),
            feature_code=normalize_label(payload.feature_code, "feature_code", max_length=120),
            endpoint=self._safe_endpoint(payload.endpoint),
            method=normalize_label(payload.method, "method", max_length=16),
            status_code=payload.status_code,
            credit_cost=payload.credit_cost,
            request_count=payload.request_count,
            pass_lookup_hash=validate_safe_hash(payload.pass_lookup_hash, "pass_lookup_hash"),
            workspace_id_hash=validate_safe_hash(payload.workspace_id_hash, "workspace_id_hash"),
            api_key_hash=validate_safe_hash(payload.api_key_hash, "api_key_hash"),
            session_id_hash=validate_safe_hash(payload.session_id_hash, "session_id_hash"),
            device_binding_id=validate_safe_hash(payload.device_binding_id, "device_binding_id"),
            telegram_binding_id=validate_safe_hash(
                payload.telegram_binding_id, "telegram_binding_id"
            ),
            sdk_client=normalize_label(payload.sdk_client, "sdk_client", max_length=80),
            client_kind=normalize_label(payload.client_kind, "client_kind", max_length=64),
            source_component=require_label(
                payload.source_component, "source_component", max_length=120
            ),
            risk_level=normalize_label(payload.risk_level, "risk_level", max_length=32),
            policy_decision=normalize_label(
                payload.policy_decision, "policy_decision", max_length=64
            ),
            denial_reason=normalize_label(payload.denial_reason, "denial_reason", max_length=160),
            metadata_json=payload.metadata_json,
            created_at=utcnow(),
        )

    def _safe_endpoint(self, endpoint: str | None) -> str | None:
        if endpoint is None:
            return None
        cleaned = endpoint.strip()
        if not cleaned:
            return None
        lowered = cleaned.lower()
        if any(term in lowered for term in FORBIDDEN_USAGE_TERMS):
            raise ValueError("endpoint contains sensitive material")
        if "://" in cleaned or "?" in cleaned:
            raise ValueError("endpoint must be a route template without scheme or query string")
        return cleaned[:200]

    def _emit_outbox_event(self, event: MetricUsageEvent) -> None:
        if self.outbox is None:
            return
        self.outbox.enqueue_event(
            event_type="metric.usage.recorded",
            aggregate_type="metric_usage",
            aggregate_id=event.id,
            payload_json={
                "event_id": event.id,
                "event_type": event.event_type,
                "decision": event.decision,
                "metric_group": event.metric_group,
                "metric_name": event.metric_name,
                "recorded_at": event.recorded_at.isoformat(),
                "credit_cost": event.credit_cost,
                "request_count": event.request_count,
            },
            target_stores=["clickhouse", "audit"],
        )
