import time

from fastapi import APIRouter, FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "path"])
SIGNAL_LATENCY = Histogram("signal_generation_latency_seconds", "Signal generation latency", ["source"])
TASK_DURATION = Histogram("task_duration_seconds", "Task runtime duration", ["task_name", "status"])
TASK_FAILURES = Counter("task_failures_total", "Task failure count", ["task_name"])
DELIVERY_PUBLISH_EVENTS = Counter(
    "delivery_publish_events_total",
    "Delivery publish events by status/reason",
    ["status", "reason"],
)
ONCHAIN_PROVIDER_PROBE_EVENTS = Counter(
    "onchain_provider_probe_events_total",
    "On-chain provider probe outcomes",
    ["outcome"],
)

OBS_RUNTIME_SEVERITY_SCORE = Gauge(
    "obs_runtime_severity_score",
    "Operational runtime severity score",
)
OBS_RUNTIME_DEGRADED_MODE_ACTIVE = Gauge(
    "obs_runtime_degraded_mode_active",
    "Whether degraded mode is active (1=yes,0=no)",
)
OBS_PROVIDER_SHARE = Gauge(
    "obs_provider_share",
    "Dominant provider share for recent onchain observations",
    ["provider"],
)
OBS_DELIVERY_FAILURES_24H = Gauge(
    "obs_delivery_failures_24h",
    "Delivery failures in the last 24h",
)
OBS_RECOVERY_UNRESOLVED_CRITICAL_FINDINGS = Gauge(
    "obs_recovery_unresolved_critical_findings",
    "Unresolved critical recovery findings",
)
OBS_CITADEL_RUNTIME_HEALTH = Gauge(
    "obs_citadel_runtime_health",
    "Citadel runtime health proxy (1 healthy, 0 degraded)",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        method = request.method
        path = request.url.path
        status = str(response.status_code)
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
        return response


def attach_metrics(app: FastAPI) -> None:
    app.add_middleware(MetricsMiddleware)

    router = APIRouter(tags=["metrics"])

    @router.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(router)


def observe_signal_latency(*, source: str, duration_seconds: float) -> None:
    SIGNAL_LATENCY.labels(source=source).observe(duration_seconds)


def observe_task_duration(*, task_name: str, status: str, duration_seconds: float) -> None:
    TASK_DURATION.labels(task_name=task_name, status=status).observe(duration_seconds)


def increment_task_failure(*, task_name: str) -> None:
    TASK_FAILURES.labels(task_name=task_name).inc()


def increment_delivery_publish_event(*, status: str, reason: str = "none") -> None:
    DELIVERY_PUBLISH_EVENTS.labels(status=status, reason=reason).inc()


def increment_onchain_provider_probe_event(*, outcome: str) -> None:
    ONCHAIN_PROVIDER_PROBE_EVENTS.labels(outcome=outcome).inc()


def set_observability_runtime_metrics(
    *,
    severity_score: int,
    degraded_mode_active: bool,
    provider_name: str,
    provider_share: float,
    delivery_failures_24h: int,
    unresolved_critical_findings: int,
    citadel_runtime_healthy: bool,
) -> None:
    OBS_RUNTIME_SEVERITY_SCORE.set(float(max(0, severity_score)))
    OBS_RUNTIME_DEGRADED_MODE_ACTIVE.set(1.0 if degraded_mode_active else 0.0)
    OBS_PROVIDER_SHARE.labels(provider=(provider_name or "unknown")).set(max(0.0, min(1.0, float(provider_share))))
    OBS_DELIVERY_FAILURES_24H.set(float(max(0, delivery_failures_24h)))
    OBS_RECOVERY_UNRESOLVED_CRITICAL_FINDINGS.set(float(max(0, unresolved_critical_findings)))
    OBS_CITADEL_RUNTIME_HEALTH.set(1.0 if citadel_runtime_healthy else 0.0)
