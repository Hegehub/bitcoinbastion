import time

from fastapi import APIRouter, FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "path"])
SIGNAL_LATENCY = Histogram("signal_generation_latency_seconds", "Signal generation latency", ["source"])
TASK_DURATION = Histogram("task_duration_seconds", "Task runtime duration", ["task_name", "status"])
TASK_FAILURES = Counter("task_failures_total", "Task failure count", ["task_name"])


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start = time.perf_counter()
        response = await call_next(request)
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
