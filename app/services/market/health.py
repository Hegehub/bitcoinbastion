from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.market_provider_health import MarketProviderHealth
from app.services.market.confidence import provider_confidence


def update_provider_health(
    db: Session,
    provider_name: str,
    success: bool,
    latency_ms: int | None,
    status_code: int | None = None,
    error: str | None = None,
) -> MarketProviderHealth:
    row = db.execute(
        select(MarketProviderHealth).where(MarketProviderHealth.provider_name == provider_name)
    ).scalar_one_or_none()
    if row is None:
        row = MarketProviderHealth(provider_name=provider_name)
        db.add(row)
        db.flush()
    now = datetime.now(UTC)
    if success:
        row.success_count += 1
        row.consecutive_failures = 0
        row.last_success_at = now
        row.last_error = None
    else:
        row.failure_count += 1
        row.consecutive_failures += 1
        row.last_failure_at = now
        row.last_error = error
    row.last_status_code = status_code
    if latency_ms is not None:
        row.avg_latency_ms = (
            latency_ms
            if row.avg_latency_ms is None
            else ((row.avg_latency_ms * 0.8) + (latency_ms * 0.2))
        )
    row.provider_confidence = provider_confidence(
        row.success_count, row.failure_count, row.consecutive_failures, row.avg_latency_ms
    )
    row.is_degraded = row.provider_confidence < 0.45 or row.consecutive_failures >= 3
    return row
