from datetime import datetime

from app.core.telemetry import OBSERVABILITY_METRIC_NAMES, bounded_label, validate_bounded_labels
from app.db.models.observability_health import BackgroundJobHealth
from app.schemas.health import BackgroundJobHealthOut, ProviderHealthSnapshotOut, TelegramHealthOut
from app.services.observability.runtime_status_service import RuntimeStatusService


def test_provider_health_calculation_degrades_on_failures_and_latency() -> None:
    svc = RuntimeStatusService()
    assert (
        svc.calculate_provider_state(
            consecutive_failures=0, provider_confidence=0.9, avg_latency_ms=100, backoff_until=None
        )
        == "healthy"
    )
    assert (
        svc.calculate_provider_state(
            consecutive_failures=1, provider_confidence=0.9, avg_latency_ms=100, backoff_until=None
        )
        == "degraded"
    )
    assert (
        svc.calculate_provider_state(
            consecutive_failures=5, provider_confidence=0.9, avg_latency_ms=100, backoff_until=None
        )
        == "critical"
    )
    assert (
        svc.calculate_provider_state(
            consecutive_failures=0, provider_confidence=0.9, avg_latency_ms=6000, backoff_until=None
        )
        == "degraded"
    )


def test_job_monitoring_marks_failed_retried_job_critical() -> None:
    row = BackgroundJobHealth(
        job_name="signals.publish", success=False, retry_count=3, failure_reason="timeout"
    )
    assert RuntimeStatusService().calculate_job_state(row) == "critical"


def test_degraded_state_generation_for_provider_job_and_telegram() -> None:
    now = datetime.utcnow()
    degraded = RuntimeStatusService().degraded_components(
        providers=[
            ProviderHealthSnapshotOut(
                provider_name="rss",
                provider_type="RSS",
                health_state="degraded",
                last_failure_at=now,
            )
        ],
        jobs=[
            BackgroundJobHealthOut(
                job_name="news.fetch", success=False, retry_count=1, health_state="degraded"
            )
        ],
        telegram=TelegramHealthOut(
            health_state="degraded", last_publish_failure=now, delivery_failures=1
        ),
    )
    components = {item.affected_component for item in degraded}
    assert "provider:RSS:rss" in components
    assert "job:news.fetch" in components
    assert "telegram" in components
    assert all(item.operator_attention_required for item in degraded)


def test_bounded_labels_validation_rejects_unbounded_values() -> None:
    assert bounded_label("provider", "https://example.com/article") == "unknown"
    assert validate_bounded_labels(
        {"provider": "rss", "job_name": "free-text-job", "ignored": "value"}
    ) == {"provider": "rss", "job_name": "unknown"}


def test_metrics_registration_contains_required_names() -> None:
    required = {
        "rss_fetch_total",
        "background_job_duration_seconds",
        "operator_reviews_total",
        "telegram_publication_failures_total",
    }
    assert required.issubset(set(OBSERVABILITY_METRIC_NAMES))
