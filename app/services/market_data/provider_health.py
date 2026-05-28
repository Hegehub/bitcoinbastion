from __future__ import annotations
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models.provider_health_record import ProviderHealthRecord
from app.services.market_data.confidence import calculate_provider_confidence


def record_provider_result(db: Session, provider: str, success: bool, latency_ms: int | None, status_code: int | None = None, error: str | None = None) -> ProviderHealthRecord:
    row = db.execute(select(ProviderHealthRecord).where(ProviderHealthRecord.provider == provider)).scalar_one_or_none()
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
        row.avg_latency_ms = latency_ms if row.avg_latency_ms is None else ((row.avg_latency_ms * 0.8) + (latency_ms * 0.2))
    row.is_degraded = row.failure_count > row.success_count and row.failure_count >= 3
    row.provider_confidence = calculate_provider_confidence(row.success_count, row.failure_count, row.avg_latency_ms, row.is_degraded)
    return row
