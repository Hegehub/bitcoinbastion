import time

from fastapi import APIRouter, FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "path"])
BASTION_HTTP_REQUESTS_TOTAL = Counter("bastion_http_requests_total", "Total Bastion HTTP requests", ["endpoint", "status"])
BASTION_HTTP_REQUEST_DURATION_SECONDS = Histogram("bastion_http_request_duration_seconds", "Bastion HTTP request duration", ["endpoint", "status"])
SIGNAL_LATENCY = Histogram("signal_generation_latency_seconds", "Signal generation latency", ["source"])
TASK_DURATION = Histogram("task_duration_seconds", "Task runtime duration", ["task_name", "status"])
TASK_FAILURES = Counter("task_failures_total", "Task failure count", ["task_name"])
DELIVERY_PUBLISH_EVENTS = Counter(
    "delivery_publish_events_total",
    "Delivery publish events by status/reason",
    ["status", "reason"],
)

BOUNDED_LABELS = {"provider", "provider_type", "signal_type", "job_name", "status", "reason_code", "endpoint", "timeframe"}
_ALLOWED_LABEL_VALUES = {
    "provider": {"rss", "btc_price", "regulatory", "official_blog", "telegram", "scheduler", "internal", "unknown"},
    "provider_type": {"news", "price", "timeline", "intelligence", "evidence", "signals", "telegram", "interface", "scheduler", "unknown"},
    "signal_type": {"news_impact", "market", "policy", "operator", "unknown"},
    "job_name": {
        "news.fetch", "news.cluster_events", "news.score_unprocessed", "market.collect_btc_price",
        "market.build_candles", "market.calculate_price_impact", "news.calculate_price_impact",
        "intelligence.attribute_candles", "intelligence.refresh_source_reputation", "intelligence.refresh_patterns",
        "intelligence.refresh_similarity", "intelligence.update_news_shock_index", "signals.create_candidates",
        "signals.create_from_news_impact", "signals.publish", "evidence.generate_packets",
        "evidence.generate_news_impact_evidence", "evidence.integrity_scan", "operations.health_snapshot",
        "operations.cleanup_expired", "unknown",
    },
    "status": {"success", "failure", "pending", "published", "rejected", "created", "requested", "degraded", "healthy", "critical", "unknown"},
    "reason_code": {"none", "provider_failure", "policy", "validation", "telegram_unavailable", "timeout", "backlog", "unknown"},
    "endpoint": {"health_live", "health_ready", "health_startup", "health_dependencies", "health_providers", "health_intelligence", "health_operations", "operations_status", "operations_health", "operations_providers", "operations_jobs", "operations_metrics", "operations_readiness", "operations_liveness", "operations_drills", "operations_metrics_summary", "operations_runbooks", "metrics", "other", "unknown"},
    "timeframe": {"1m", "5m", "15m", "1h", "4h", "1d", "unknown"},
}


def bounded_label(label: str, value: str | None) -> str:
    allowed = _ALLOWED_LABEL_VALUES.get(label)
    candidate = (value or "unknown").strip()
    if allowed is None:
        return "unknown"
    return candidate if candidate in allowed else "unknown"


def validate_bounded_labels(labels: dict[str, str]) -> dict[str, str]:
    return {key: bounded_label(key, value) for key, value in labels.items() if key in BOUNDED_LABELS}

ONCHAIN_PROVIDER_PROBE_EVENTS = Counter(
    "onchain_provider_probe_events_total",
    "On-chain provider probe outcomes",
    ["outcome"],
)


RSS_FETCH_TOTAL = Counter("rss_fetch_total", "RSS fetch attempts", ["provider", "status"])
RSS_FETCH_FAILURES_TOTAL = Counter("rss_fetch_failures_total", "RSS fetch failures", ["provider", "reason_code"])
BTC_PRICE_COLLECTION_TOTAL = Counter("btc_price_collection_total", "BTC price collection attempts", ["provider", "status"])
BTC_PRICE_COLLECTION_FAILURES_TOTAL = Counter("btc_price_collection_failures_total", "BTC price collection failures", ["provider", "reason_code"])
NEWS_EVENTS_CREATED_TOTAL = Counter("news_events_created_total", "News events created", ["status"])
NEWS_IMPACTS_CREATED_TOTAL = Counter("news_impacts_created_total", "News impacts created", ["status"])
CANDLE_ATTRIBUTIONS_CREATED_TOTAL = Counter("candle_attributions_created_total", "Candle attributions created", ["status"])
SIGNALS_CREATED_TOTAL = Counter("signals_created_total", "Signals created", ["signal_type", "status"])
SIGNALS_PUBLISHED_TOTAL = Counter("signals_published_total", "Signals published", ["signal_type", "status"])
SIGNALS_REJECTED_TOTAL = Counter("signals_rejected_total", "Signals rejected", ["signal_type", "reason_code"])
SIGNALS_PENDING_REVIEW_TOTAL = Gauge("signals_pending_review_total", "Signals pending operator review", ["signal_type"])
TELEGRAM_PUBLICATIONS_TOTAL = Counter("telegram_publications_total", "Telegram publication attempts", ["status"])
TELEGRAM_PUBLICATION_FAILURES_TOTAL = Counter("telegram_publication_failures_total", "Telegram publication failures", ["reason_code"])
PROVIDER_DEGRADED_TOTAL = Counter("provider_degraded_total", "Provider degraded events", ["provider", "reason_code"])
BACKGROUND_JOB_FAILURES_TOTAL = Counter("background_job_failures_total", "Background job failures", ["job_name", "reason_code"])
BACKGROUND_JOB_DURATION_SECONDS = Histogram("background_job_duration_seconds", "Background job duration seconds", ["job_name", "status"])
OPERATOR_REVIEWS_TOTAL = Counter("operator_reviews_total", "Operator reviews", ["status", "reason_code"])
BASTION_NEWS_FETCH_TOTAL = Counter("bastion_news_fetch_total", "Bastion news fetch attempts", ["provider", "status"])
BASTION_NEWS_FETCH_FAILURES_TOTAL = Counter("bastion_news_fetch_failures_total", "Bastion news fetch failures", ["provider", "status"])
BASTION_PROVIDER_HEALTH_SCORE = Gauge("bastion_provider_health_score", "Bastion provider health score", ["provider"])
BASTION_PRICE_PROVIDER_HEALTH_SCORE = Gauge("bastion_price_provider_health_score", "Bastion price provider health score", ["provider"])
BASTION_NEWS_EVENTS_TOTAL = Counter("bastion_news_events_total", "Bastion news events", ["status"])
BASTION_CANDLE_ATTRIBUTIONS_TOTAL = Counter("bastion_candle_attributions_total", "Bastion candle attributions", ["status"])
BASTION_SIGNALS_GENERATED_TOTAL = Counter("bastion_signals_generated_total", "Bastion generated signals", ["signal_type", "status"])
BASTION_SIGNALS_PUBLISHED_TOTAL = Counter("bastion_signals_published_total", "Bastion published signals", ["signal_type", "status"])
BASTION_EVIDENCE_PACKETS_TOTAL = Counter("bastion_evidence_packets_total", "Bastion evidence packets", ["status"])
BASTION_REPLAY_REQUESTS_TOTAL = Counter("bastion_replay_requests_total", "Bastion replay requests", ["status"])
BASTION_OPERATOR_REVIEWS_TOTAL = Counter("bastion_operator_reviews_total", "Bastion operator reviews", ["status"])
BASTION_BACKGROUND_JOBS_TOTAL = Counter("bastion_background_jobs_total", "Bastion background jobs", ["job_name", "status"])
BASTION_BACKGROUND_JOB_FAILURES_TOTAL = Counter("bastion_background_job_failures_total", "Bastion background job failures", ["job_name", "status"])
BASTION_PROVIDER_DEGRADED_TOTAL = Counter("bastion_provider_degraded_total", "Bastion provider degraded events", ["provider", "status"])

NEWS_ARTICLES_PROCESSED_TOTAL = Counter("news_articles_processed_total", "News articles processed", ["provider_type", "status"])
MARKET_PRICE_POINTS_TOTAL = Counter("market_price_points_total", "Market price points collected", ["provider_type", "status"])
BTC_CANDLES_GENERATED_TOTAL = Counter("btc_candles_generated_total", "BTC candles generated", ["timeframe", "status"])
PRICE_IMPACTS_GENERATED_TOTAL = Counter("price_impacts_generated_total", "Price impacts generated", ["status"])
CANDLE_ATTRIBUTIONS_GENERATED_TOTAL = Counter("candle_attributions_generated_total", "Candle attributions generated", ["timeframe", "status"])
HISTORICAL_SIMILARITY_QUERIES_TOTAL = Counter("historical_similarity_queries_total", "Historical similarity queries", ["status"])
SIGNALS_GENERATED_TOTAL = Counter("signals_generated_total", "Signals generated", ["signal_type", "status"])
SIGNALS_BLOCKED_TOTAL = Counter("signals_blocked_total", "Signals blocked", ["signal_type", "status"])
PROVIDER_HEALTH_FAILURES_TOTAL = Counter("provider_health_failures_total", "Provider health failures", ["provider_type", "status"])
TIMELINE_BUILD_FAILURES_TOTAL = Counter("timeline_build_failures_total", "Timeline build failures", ["status"])
CRONJOB_FAILURES_TOTAL = Counter("cronjob_failures_total", "CronJob failures", ["job_name", "status"])
DR_RECOVERY_RUNS_TOTAL = Counter("dr_recovery_runs_total", "Disaster recovery runs", ["status"])
BACKUP_VALIDATION_RUNS_TOTAL = Counter("backup_validation_runs_total", "Backup validation runs", ["status"])

OBSERVABILITY_METRIC_NAMES = [
    "rss_fetch_total", "rss_fetch_failures_total", "btc_price_collection_total",
    "btc_price_collection_failures_total", "news_events_created_total", "news_impacts_created_total",
    "candle_attributions_created_total", "signals_created_total", "signals_published_total",
    "signals_rejected_total", "signals_pending_review_total", "evidence_packets_generated_total",
    "evidence_replay_requests_total", "telegram_publications_total", "telegram_publication_failures_total",
    "provider_degraded_total", "background_job_failures_total", "background_job_duration_seconds",
    "operator_reviews_total",
    "bastion_http_requests_total", "bastion_http_request_duration_seconds", "bastion_news_fetch_total",
    "bastion_news_fetch_failures_total", "bastion_provider_health_score", "bastion_price_provider_health_score",
    "bastion_news_events_total", "bastion_candle_attributions_total", "bastion_signals_generated_total",
    "bastion_signals_published_total", "bastion_evidence_packets_total", "bastion_replay_requests_total",
    "bastion_operator_reviews_total", "bastion_background_jobs_total", "bastion_background_job_failures_total",
    "bastion_provider_degraded_total",

    "news_articles_processed_total", "market_price_points_total", "btc_candles_generated_total",
    "price_impacts_generated_total", "candle_attributions_generated_total", "historical_similarity_queries_total",
    "signals_generated_total", "signals_blocked_total", "provider_health_failures_total",
    "timeline_build_failures_total", "cronjob_failures_total", "dr_recovery_runs_total",
    "backup_validation_runs_total",
]

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
OBS_PROVIDER_HEALTH_STATE = Gauge(
    "obs_provider_health_state",
    "Provider health state by provider type/name",
    ["provider_type", "provider_name", "state", "is_fallback", "is_mock"],
)
OBS_PROVIDER_LATENCY_MS = Gauge("obs_provider_latency_ms", "Provider probe latency ms", ["provider_type", "provider_name"])
OBS_PROVIDER_FALLBACK_ACTIVE = Gauge("obs_provider_fallback_active", "Provider fallback active (1/0)", ["provider_type", "provider_name"])
OBS_PROVIDER_CONFIDENCE = Gauge("obs_provider_confidence", "Provider confidence", ["provider_type", "provider_name"])
OBS_PROVIDER_LAST_SUCCESS_AGE_SECONDS = Gauge(
    "obs_provider_last_success_age_seconds", "Provider age since last successful evidence", ["provider_type", "provider_name"]
)
OBS_PROVIDER_FAILURE_COUNT = Counter("obs_provider_failure_total", "Provider failure count", ["provider_type", "provider_name", "error_type"])


def _safe_provider_labels(provider_type: str, provider_name: str) -> tuple[str, str]:
    safe_type = provider_type if provider_type in {"bitcoin", "rss", "delivery", "unknown"} else "unknown"
    safe_name = provider_name[:64] if provider_name else "unknown"
    return safe_type, safe_name


def _safe_endpoint_label(path: str) -> str:
    mapping = {
        "/health/live": "health_live",
        "/health/ready": "health_ready",
        "/health/startup": "health_startup",
        "/health/dependencies": "health_dependencies",
        "/health/providers": "health_providers",
        "/health/intelligence": "health_intelligence",
        "/health/operations": "health_operations",
        "/api/v1/operations/status": "operations_status",
        "/api/v1/operations/health": "operations_health",
        "/api/v1/operations/providers": "operations_providers",
        "/api/v1/operations/jobs": "operations_jobs",
        "/api/v1/operations/metrics": "operations_metrics",
        "/api/v1/operations/readiness": "operations_readiness",
        "/api/v1/operations/liveness": "operations_liveness",
        "/api/v1/operations/drills": "operations_drills",
        "/api/v1/operations/metrics-summary": "operations_metrics_summary",
        "/api/v1/operations/runbooks": "operations_runbooks",
        "/metrics": "metrics",
    }
    return mapping.get(path, "other")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        method = request.method
        path = request.url.path
        status = str(response.status_code)
        endpoint = _safe_endpoint_label(path)
        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration)
        BASTION_HTTP_REQUESTS_TOTAL.labels(endpoint=endpoint, status=bounded_label("status", "success" if response.status_code < 500 else "failure")).inc()
        BASTION_HTTP_REQUEST_DURATION_SECONDS.labels(endpoint=endpoint, status=bounded_label("status", "success" if response.status_code < 500 else "failure")).observe(duration)
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


def set_provider_health_state_metric(
    *, provider_type: str, provider_name: str, healthy: bool, is_fallback: bool, is_mock: bool
) -> None:
    safe_type, safe_name = _safe_provider_labels(provider_type, provider_name)
    safe_state = "healthy" if healthy else "unhealthy"
    OBS_PROVIDER_HEALTH_STATE.labels(
        provider_type=safe_type,
        provider_name=safe_name,
        state=safe_state,
        is_fallback="true" if is_fallback else "false",
        is_mock="true" if is_mock else "false",
    ).set(1.0)


def set_provider_health_detail_metrics(
    *, provider_type: str, provider_name: str, latency_ms: int, is_fallback: bool, confidence: float, last_success_age_seconds: int
) -> None:
    safe_type, safe_name = _safe_provider_labels(provider_type, provider_name)
    OBS_PROVIDER_LATENCY_MS.labels(provider_type=safe_type, provider_name=safe_name).set(float(max(0, latency_ms)))
    OBS_PROVIDER_FALLBACK_ACTIVE.labels(provider_type=safe_type, provider_name=safe_name).set(1.0 if is_fallback else 0.0)
    OBS_PROVIDER_CONFIDENCE.labels(provider_type=safe_type, provider_name=safe_name).set(max(0.0, min(1.0, confidence)))
    OBS_PROVIDER_LAST_SUCCESS_AGE_SECONDS.labels(provider_type=safe_type, provider_name=safe_name).set(float(max(0, last_success_age_seconds)))


def increment_provider_failure_metric(*, provider_type: str, provider_name: str, error_type: str | None) -> None:
    safe_type, safe_name = _safe_provider_labels(provider_type, provider_name)
    OBS_PROVIDER_FAILURE_COUNT.labels(provider_type=safe_type, provider_name=safe_name, error_type=(error_type or "none")[:64]).inc()


def increment_observability_counter(metric_name: str, **labels: str) -> None:
    metric = globals().get(metric_name)
    if metric is None:
        raise KeyError(f"Unknown observability metric: {metric_name}")
    safe = validate_bounded_labels(labels)
    metric.labels(**safe).inc()


def observe_background_job_duration(*, job_name: str, status: str, duration_seconds: float) -> None:
    BACKGROUND_JOB_DURATION_SECONDS.labels(
        job_name=bounded_label("job_name", job_name),
        status=bounded_label("status", status),
    ).observe(max(0.0, duration_seconds))
