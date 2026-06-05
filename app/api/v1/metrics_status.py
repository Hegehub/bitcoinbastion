from fastapi import APIRouter

from app.core.telemetry import BOUNDED_LABELS, OBSERVABILITY_METRIC_NAMES
from app.schemas.health import MetricsStatusOut

router = APIRouter(prefix="/metrics", tags=["metrics-status"])


@router.get("/status", response_model=MetricsStatusOut)
def metrics_status() -> MetricsStatusOut:
    return MetricsStatusOut(
        prometheus_enabled=True,
        endpoint="/metrics",
        bounded_labels=sorted(BOUNDED_LABELS),
        registered_metrics=OBSERVABILITY_METRIC_NAMES,
    )
