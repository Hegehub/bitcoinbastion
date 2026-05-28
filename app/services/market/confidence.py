from __future__ import annotations


def provider_confidence(success_count: int, failure_count: int, consecutive_failures: int, avg_latency_ms: float | None) -> float:
    value = 0.75
    value -= min(0.35, failure_count * 0.01)
    value -= min(0.25, consecutive_failures * 0.03)
    if avg_latency_ms is not None:
        if avg_latency_ms > 10000:
            value -= 0.2
        elif avg_latency_ms > 3000:
            value -= 0.08
    value += min(0.2, success_count * 0.002)
    return round(max(0.0, min(1.0, value)), 4)
