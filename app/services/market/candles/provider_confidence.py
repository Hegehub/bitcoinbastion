def calculate_provider_confidence(provider_count: int, spread_pct: float, degraded: bool) -> float:
    base = 0.35 if provider_count <= 1 else 0.65 if provider_count == 2 else 0.9
    base -= min(0.4, spread_pct / 25)
    if degraded:
        base -= 0.2
    return max(0.0, min(1.0, round(base, 4)))
