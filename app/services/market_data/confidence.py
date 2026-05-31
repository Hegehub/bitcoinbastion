from __future__ import annotations


def calculate_provider_confidence(success_count: int, failure_count: int, avg_latency_ms: float | None, is_degraded: bool) -> float:
    base = 0.7
    penalty = min(0.4, failure_count * 0.01)
    latency_penalty = 0.0 if avg_latency_ms is None else (0.05 if avg_latency_ms > 3000 else 0.15 if avg_latency_ms > 10000 else 0.0)
    reward = min(0.2, success_count * 0.002)
    value = base - penalty - latency_penalty + reward - (0.2 if is_degraded else 0.0)
    return max(0.0, min(1.0, round(value, 4)))
