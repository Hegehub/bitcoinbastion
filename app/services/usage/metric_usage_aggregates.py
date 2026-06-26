from __future__ import annotations

from app.services.usage.metric_usage_models import MetricUsageSummary


def build_usage_summary(values: dict[str, int]) -> MetricUsageSummary:
    return MetricUsageSummary(
        total_requests=values.get("total_requests", 0),
        total_credits=values.get("total_credits", 0),
        allowed=values.get("allowed", 0),
        denied=values.get("denied", 0),
        degraded=values.get("degraded", 0),
        cached=values.get("cached", 0),
        skipped=values.get("skipped", 0),
        event_count=values.get("event_count", 0),
    )
