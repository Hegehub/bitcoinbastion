from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.models.time_utils import utcnow
from app.core.telemetry import BOUNDED_LABELS, OBSERVABILITY_METRIC_NAMES
from app.db.repositories.provider_source_health_timeseries_repository import (
    ProviderSourceHealthTimeSeriesRepository,
)
from app.services.usage import MetricUsageRepository, MetricUsageService
from app.db.session import get_db
from app.schemas.health import MetricsStatusOut

router = APIRouter(prefix="/metrics", tags=["metrics-status"])


class HealthSnapshotOut(BaseModel):
    observed_at: str
    provider_key: str | None = None
    source_key: str | None = None
    source_type: str | None = None
    domain: str
    status: str
    health_score: float | None = None
    confidence_score: float | None = None
    latency_ms: int | None = None
    error_rate: float | None = None
    success_count: int
    failure_count: int
    degraded_reason: str | None = None
    runtime_mode: str
    is_degraded: bool


class HealthHistoryOut(BaseModel):
    items: list[HealthSnapshotOut]
    limit: int = Field(ge=1, le=500)


def _snapshot_out(snapshot: object) -> HealthSnapshotOut:
    return HealthSnapshotOut(
        observed_at=getattr(snapshot, "observed_at").isoformat(),
        provider_key=getattr(snapshot, "provider_key", None),
        source_key=getattr(snapshot, "source_key", None),
        source_type=getattr(snapshot, "source_type", None),
        domain=getattr(snapshot, "domain"),
        status=getattr(snapshot, "status"),
        health_score=getattr(snapshot, "health_score"),
        confidence_score=getattr(snapshot, "confidence_score"),
        latency_ms=getattr(snapshot, "latency_ms"),
        error_rate=getattr(snapshot, "error_rate"),
        success_count=getattr(snapshot, "success_count"),
        failure_count=getattr(snapshot, "failure_count"),
        degraded_reason=getattr(snapshot, "degraded_reason"),
        runtime_mode=getattr(snapshot, "runtime_mode"),
        is_degraded=getattr(snapshot, "is_degraded"),
    )


class MetricUsageSummaryOut(BaseModel):
    window: str
    total_requests: int
    total_credits: int
    allowed: int
    denied: int
    degraded: int
    cached: int
    skipped: int
    event_count: int
    top_metric_groups: list[dict[str, object]] = Field(default_factory=list)
    degraded_mode: bool = False


@router.get("/status", response_model=MetricsStatusOut)
def metrics_status() -> MetricsStatusOut:
    return MetricsStatusOut(
        prometheus_enabled=True,
        endpoint="/metrics",
        bounded_labels=sorted(BOUNDED_LABELS),
        registered_metrics=OBSERVABILITY_METRIC_NAMES,
    )


@router.get(
    "/provider-health/history",
    response_model=HealthHistoryOut,
    summary="Provider health time-series history.",
)
def provider_health_history(
    provider_key: str = Query(..., min_length=1, max_length=120),
    from_ts: datetime | None = Query(None, alias="from"),
    to_ts: datetime | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    domain: str | None = Query(None, min_length=1, max_length=64),
    status: str | None = Query(None, min_length=1, max_length=32),
    is_degraded: bool | None = None,
    db: Session = Depends(get_db),
) -> HealthHistoryOut:
    upper = to_ts or utcnow()
    lower = from_ts or (upper - timedelta(hours=24))
    if lower > upper:
        raise HTTPException(status_code=422, detail="from must be before to")
    repo = ProviderSourceHealthTimeSeriesRepository(db)
    items = repo.provider_history(
        provider_key,
        lower,
        upper,
        limit,
        domain=domain,
        status=status,
        is_degraded=is_degraded,
    )
    return HealthHistoryOut(items=[_snapshot_out(item) for item in items], limit=limit)


@router.get(
    "/source-health/history",
    response_model=HealthHistoryOut,
    summary="Source health time-series history.",
)
def source_health_history(
    source_key: str = Query(..., min_length=1, max_length=120),
    from_ts: datetime | None = Query(None, alias="from"),
    to_ts: datetime | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    domain: str | None = Query(None, min_length=1, max_length=64),
    status: str | None = Query(None, min_length=1, max_length=32),
    is_degraded: bool | None = None,
    db: Session = Depends(get_db),
) -> HealthHistoryOut:
    upper = to_ts or utcnow()
    lower = from_ts or (upper - timedelta(hours=24))
    if lower > upper:
        raise HTTPException(status_code=422, detail="from must be before to")
    repo = ProviderSourceHealthTimeSeriesRepository(db)
    items = repo.source_history(
        source_key,
        lower,
        upper,
        limit,
        domain=domain,
        status=status,
        is_degraded=is_degraded,
    )
    return HealthHistoryOut(items=[_snapshot_out(item) for item in items], limit=limit)


@router.get(
    "/provider-health/latest",
    response_model=HealthSnapshotOut,
    summary="Latest provider health time-series snapshot.",
)
def latest_provider_health(
    provider_key: str = Query(..., min_length=1, max_length=120),
    db: Session = Depends(get_db),
) -> HealthSnapshotOut:
    snapshot = ProviderSourceHealthTimeSeriesRepository(db).latest_provider_snapshot(provider_key)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="provider health snapshot not found")
    return _snapshot_out(snapshot)


@router.get(
    "/source-health/latest",
    response_model=HealthSnapshotOut,
    summary="Latest source health time-series snapshot.",
)
def latest_source_health(
    source_key: str = Query(..., min_length=1, max_length=120),
    db: Session = Depends(get_db),
) -> HealthSnapshotOut:
    snapshot = ProviderSourceHealthTimeSeriesRepository(db).latest_source_snapshot(source_key)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="source health snapshot not found")
    return _snapshot_out(snapshot)


@router.get(
    "/usage",
    response_model=MetricUsageSummaryOut,
    summary="Metric/API usage summary for a bounded time window.",
)
def metric_usage_summary(
    window_hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
) -> MetricUsageSummaryOut:
    upper = utcnow()
    lower = upper - timedelta(hours=window_hours)
    service = MetricUsageService(MetricUsageRepository(db))
    summary = service.get_usage_summary(lower, upper)
    return MetricUsageSummaryOut(
        window=f"{window_hours}h",
        total_requests=summary.total_requests,
        total_credits=summary.total_credits,
        allowed=summary.allowed,
        denied=summary.denied,
        degraded=summary.degraded,
        cached=summary.cached,
        skipped=summary.skipped,
        event_count=summary.event_count,
        top_metric_groups=[],
        degraded_mode=False,
    )
