from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.provider_health_record import ProviderHealthRecord
from app.services.events.domain_event_publisher import publish_domain_event
from app.services.market_data.confidence import calculate_provider_confidence


def record_provider_result(
    db: Session,
    provider: str,
    success: bool,
    latency_ms: int | None,
    status_code: int | None = None,
    error: str | None = None,
) -> ProviderHealthRecord:
    row = db.execute(
        select(ProviderHealthRecord).where(ProviderHealthRecord.provider == provider)
    ).scalar_one_or_none()
    previous_degraded = bool(row.is_degraded) if row is not None else False
    if row is None:
        row = ProviderHealthRecord(provider=provider)
        db.add(row)
        db.flush()
    now = datetime.now(UTC)
    if success:
        row.success_count += 1
        row.last_success_at = now
        row.last_error = None
    else:
        row.failure_count += 1
        row.last_failure_at = now
        row.last_error = error
    row.last_status_code = status_code
    if latency_ms is not None:
        row.avg_latency_ms = (
            latency_ms
            if row.avg_latency_ms is None
            else ((row.avg_latency_ms * 0.8) + (latency_ms * 0.2))
        )
    row.is_degraded = row.failure_count > row.success_count and row.failure_count >= 3
    row.provider_confidence = calculate_provider_confidence(
        row.success_count, row.failure_count, row.avg_latency_ms, row.is_degraded
    )
    if row.is_degraded and not previous_degraded:
        publish_domain_event(
            db,
            "provider.degraded",
            {
                "provider_name": provider,
                "provider_type": "market_data",
                "previous_status": "degraded" if previous_degraded else "available",
                "current_status": "degraded",
                "confidence": row.provider_confidence,
                "data_age_seconds": None,
                "fallback_active": True,
                "stale": False,
                "degraded": True,
                "observed_at": now.isoformat(),
                "limitations": ["Provider degradation is visible to downstream consumers."],
            },
            aggregate_type="provider_health",
            aggregate_id=provider,
            source="provider_health",
            idempotency_key=f"provider.degraded:provider_health:{provider}:{row.failure_count}",
        )
    elif previous_degraded and not row.is_degraded:
        publish_domain_event(
            db,
            "provider.recovered",
            {
                "provider_name": provider,
                "provider_type": "market_data",
                "previous_status": "degraded",
                "current_status": "available",
                "confidence": row.provider_confidence,
                "data_age_seconds": None,
                "fallback_active": False,
                "stale": False,
                "degraded": False,
                "observed_at": now.isoformat(),
                "limitations": ["Provider recovery is based on the latest provider result."],
            },
            aggregate_type="provider_health",
            aggregate_id=provider,
            source="provider_health",
            idempotency_key=f"provider.recovered:provider_health:{provider}:{row.success_count}",
        )
    return row
