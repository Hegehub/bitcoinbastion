def evaluate_integrity(provider_count: int, spread_pct: float, is_partial: bool) -> tuple[str, str]:
    if provider_count == 0:
        return "missing_provider_data", "no_providers"
    if spread_pct > 2.5:
        return "degraded", f"provider_divergence:{round(spread_pct,4)}"
    if is_partial:
        return "partial", "window_open"
    return "valid", ""


def calculate_integrity_score(
    provider_count: int, point_count: int, spread_pct: float, degraded: bool
) -> float:
    score = 0.3 + min(0.4, provider_count * 0.15) + min(0.2, point_count * 0.01)
    score -= min(0.4, spread_pct / 20)
    if degraded:
        score -= 0.2
    return max(0.0, min(1.0, round(score, 4)))
